

import logging

def search_documents(user_question, doc_ids=None, compound_id=None):

    import os
    import base64
    from openai import AzureOpenAI
    import concurrent.futures
    from db_helper import DBConnectionManager

    endpoint = os.getenv("ENDPOINT_URL")
    deployment = os.getenv("DEPLOYMENT_NAME")
    search_endpoint = os.getenv("SEARCH_ENDPOINT")
    search_key =   os.getenv("SEARCH_KEY")
    subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    # If no doc_ids provided but compound_id is provided, fetch all doc_ids for that compound
    if doc_ids is None or len(doc_ids) == 0:
        if compound_id:
            # Get all document IDs for this compound that have been indexed
            db = DBConnectionManager.get_instance()
            results = db.select(
                "SELECT id FROM ipx_documents WHERE compound_id = ? AND status = 'indexed'", 
                (compound_id,)
            )
            doc_ids = [str(result['id']) for result in results] if results else []
            logging.info(f"Found {len(doc_ids)} indexed documents for compound {compound_id}")
        else:
            # Neither doc_ids nor compound_id provided
            logging.warning("No document IDs or compound ID provided for search")
            return "I don't have any relevant documents to search through.", {}

    # Initialize Azure OpenAI client with key-based authentication
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=subscription_key,
        api_version="2025-01-01-preview",
    )

    # IMAGE_PATH = "YOUR_IMAGE_PATH"
    # encoded_image = base64.b64encode(open(IMAGE_PATH, 'rb').read()).decode('ascii')

    #Prepare the chat prompt
    chat_prompt = [
        {
            "role": "system",
            "content": "You are an AI assistant that helps people find information."
        },
        {
            "role": "user",
            "content": user_question
        }
    ]

    # Include speech result if speech is enabled
    messages = chat_prompt

    for msg in messages:
        if not isinstance(msg.get("content", ""), str):
            logging.warning(f"Invalid message: {msg}")

    # Function to search a single document index
    def search_single_index(doc_id):
        try:
            # Format the index name according to our pattern
            index_name = f"index-doc-{doc_id}"
            logging.info(f"Searching in index: {index_name}")
            
            # Create a completion for this specific document index
            completion = client.chat.completions.create(
                model=deployment,
                messages=messages,
                max_tokens=800,
                temperature=1,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=False,
                extra_body={
                    "data_sources": [{
                        "type": "azure_search",
                        "parameters": {
                            "endpoint": f"{search_endpoint}",
                            "index_name": index_name,
                            "semantic_configuration": "default",
                            # "query_type": "semantic",
                            "fields_mapping": {},
                            "in_scope": True,
                            "filter": None,
                            "strictness": 3,
                            "top_n_documents": 3,  # Fewer docs per index since we're searching multiple
                            "authentication": {
                                "type": "api_key",
                                "key": f"{search_key}"
                            }
                        }
                    }]
                }
            )
            return doc_id, completion
        except Exception as e:
            logging.error(f"Error searching index for document {doc_id}: {str(e)}", exc_info=True)
            return doc_id, None
    
    # Search all document indexes concurrently
    all_results = []
    all_sources = {}
    
    if not doc_ids or len(doc_ids) == 0:
        logging.warning("No document IDs available to search")
        return "I don't have any relevant documents to search through.", {}
    
    logging.info(f"Searching across {len(doc_ids)} document indexes")
    
    # Use ThreadPoolExecutor to run searches concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(5, len(doc_ids))) as executor:
        future_to_doc_id = {executor.submit(search_single_index, doc_id): doc_id for doc_id in doc_ids}
        for future in concurrent.futures.as_completed(future_to_doc_id):
            doc_id = future_to_doc_id[future]
            try:
                doc_id, completion = future.result()
                if completion:
                    all_results.append((doc_id, completion))
            except Exception as e:
                logging.error(f"Exception processing result for document {doc_id}: {str(e)}", exc_info=True)
    
    # No valid results found
    if not all_results:
        return "I couldn't find relevant information in the documents.", {}

    # Process all results
    collected_results = []
    combined_answer = ""
    import json
    import re
    
    valid_results = []
    
    for doc_id, completion in all_results:
        try:
            raw_text = completion.to_json()
            response_json = json.loads(raw_text)
            logging.info(f"Processing result from document {doc_id}")
            
            # Function to extract doc numbers from content
            def extract_doc_numbers(text):
                # Extract all [docX] occurrences throughout the text
                doc_pattern = r'\[doc(\d+)\]'
                doc_matches = re.findall(doc_pattern, text)
                
                if doc_matches:
                    # Convert all matched doc numbers to integers
                    doc_numbers = [int(match) for match in doc_matches]
                    return doc_numbers, True
                else:
                    return [], False
            
            # Process each choice in the completion
            for choice in response_json.get('choices', []):
                content = choice.get('message', {}).get('content', '')
                
                # Extract [doc1], [doc2], ... as integers [1, 2, ...]
                doc_numbers, has_doc_pattern = extract_doc_numbers(content)
                
                # Check if this response actually has citations or is just saying "no data found"
                has_citations = False
                is_negative_response = False
                
                # Phrases that indicate no relevant info was found
                negative_phrases = [
                    "not found in the retrieved data", 
                    "couldn't find relevant information",
                    "don't have information about",
                    "no information available",
                    "no relevant information",
                    "no data on",
                    "not mentioned in"
                ]
                
                # Check if content contains any negative phrases
                if any(phrase.lower() in content.lower() for phrase in negative_phrases):
                    is_negative_response = True
                
                # Determine if the result has actual citations with content
                if has_doc_pattern:
                    all_citations = choice.get('message', {}).get('context', {}).get('citations', [])
                    if all_citations:  # If there are actual citations
                        has_citations = True
                        
                        # Add doc ID prefix to sources to avoid collisions between different documents
                        for number in doc_numbers:
                            index = number - 1  # Convert [doc1] → citations[0]
                            if 0 <= index < len(all_citations):
                                citation = all_citations[index]
                                file_title = citation.get('title', '')
                                if file_title and '_' in file_title:
                                    file_title = file_title.split('_', 1)[1]  # Remove UUID prefix
                                # Use a compound key with doc_id to avoid collisions
                                source_key = f"{doc_id}_{number}"
                                all_sources[source_key] = file_title
                
                # Only add to valid results if it has real citations and isn't just saying "not found"
                if has_citations and not is_negative_response:
                    valid_results.append((doc_id, content))
                    # Add this content to our collection
                    collected_results.append(content)
                    combined_answer += content + "\n\n"
                else:
                    logging.warning(f"Skipping empty result from document {doc_id}")
        except Exception as e:
            logging.error(f"Error processing result for document {doc_id}: {str(e)}", exc_info=True)
    
    # Check if we found any valid results with citations
    if valid_results:
        # Clean up repeated information and consolidate answer
        result = combined_answer.strip()
    else:
        # No valid results found across all indexes
        result = "I don't have information about this topic in the knowledge base. Please try a different question."
    
    return result, all_sources

