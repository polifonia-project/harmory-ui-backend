from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
from query_factory import (get_tune_given_name, get_pattern_search_query,
                           advanced_search, get_most_common_patterns_for_a_tune,
                           get_neighbour_patterns_by_tune, get_neighbour_tunes_by_pattern,
                           get_tune_data, get_tune_family_members,
                           get_patterns_in_common_between_two_tunes,
                           get_neighbour_tunes_by_common_patterns,
                           get_corpus_list, get_keys_list, get_time_sig_list,
                           get_tune_type_list, get_kg_version)

from fuzzy_search import FuzzySearch

app = Flask(__name__)
CORS(app)

BLAZEGRAPH_URL = 'https://polifonia.disi.unibo.it/harmory/sparql'

EMPTY_SEARCH_RESPONSE = {"head":{"vars":["tune_name", "genre", "artist", "id"]},"results":{"bindings":[]}}
fuzzy_search = FuzzySearch(BLAZEGRAPH_URL)


@app.route('/api/search', methods=['GET'])
def search():
    #print(request)
    # Get the query parameters from the GET request
    query_params = request.args.to_dict(flat=False)
    # Composition title based search
    search_type = query_params['searchType'][0]
    #print(query_params)
    sparql_query = ""
    if search_type == "title":
        search_term = query_params['searchTerm'][0]
        fuzzy_title_matches = fuzzy_search.get_title_best_match(search_term)
        if not fuzzy_title_matches:
            # If there are no matched titles, return an empty response.
            return jsonify(EMPTY_SEARCH_RESPONSE), 200
        else:
            # Generate the SPARQL query
            sparql_query = get_tune_given_name(fuzzy_title_matches)
    # Patters based search
    elif search_type == "pattern":
        search_term = query_params['searchTerm'][0]
        sparql_query = get_pattern_search_query(search_term)
    # Advanced search
    elif search_type == "advanced":
        matched_tuples = []
        if query_params['title'][0]:
            search_term = query_params['title'][0]
            matched_tuples = fuzzy_search.get_title_best_match(search_term)
        if query_params['title'][0] and not matched_tuples:
            # If a title is searched for and there are no matched titles, return an empty response.
            return jsonify(EMPTY_SEARCH_RESPONSE), 200
        else:
            sparql_query = advanced_search(query_params, matched_tuples)
    else:
        # Error message.
        return jsonify({'error': 'Invalid search type.'}), 501
    # Execute the SPARQL query
    response = requests.post(
        BLAZEGRAPH_URL,
        data={
            'query': sparql_query,
            'format': 'json'
        }
    )
    #print(sparql_query)
    #print(response.text)
    # Check the response status
    if response.status_code != 200:
        print(f"Error executing Sparql Query = {sparql_query}")
        print(response.text)
        return jsonify({'error': 'Failed to execute SPARQL query'}), 500
    # Return the JSON data
    return jsonify(response.json()), 200


@app.route('/api/corpus_list', methods=['GET'])
def getCorpusList():
    # Generate the SPARQL query
    sparql_query = get_corpus_list()
    # Execute the SPARQL query
    response = requests.post(
        BLAZEGRAPH_URL,
        data={
            'query': sparql_query,
            'format': 'json'
        }
    )
    #print(sparql_query)
    #print(response.text)
    # Check the response status
    if response.status_code != 200:
        return jsonify({'error': 'Failed to execute SPARQL query'}), 500
    corpusJSON = response.json()
    corpus_list = [item['corpus']['value'] for item in
                 corpusJSON['results']['bindings']]
    #print(corpus_list)
    # Return the JSON data
    return jsonify(corpus_list), 200


@app.route('/api/keys_list', methods=['GET'])
def getKeysList():
    # Generate the SPARQL query
    sparql_query = get_keys_list()
    # Execute the SPARQL query
    response = requests.post(
        BLAZEGRAPH_URL,
        data={
            'query': sparql_query,
            'format': 'json'
        }
    )
    #print(sparql_query)
    #print(response.text)
    # Check the response status
    if response.status_code != 200:
        return jsonify({'error': 'Failed to execute SPARQL query'}), 500
    keysJSON = response.json()
    keys_list = [item['key']['value'] for item in
                 keysJSON['results']['bindings']]
    #print(keys_list)
    # Return the JSON data
    return jsonify(keys_list), 200


@app.route('/api/time_sig_list', methods=['GET'])
def getTimeSignatureList():
    # Generate the SPARQL query
    sparql_query = get_time_sig_list()
    # Execute the SPARQL query
    response = requests.post(
        BLAZEGRAPH_URL,
        data={
            'query': sparql_query,
            'format': 'json'
        }
    )
    #print(sparql_query)
    #print(response.text)
    # Check the response status
    if response.status_code != 200:
        return jsonify({'error': 'Failed to execute SPARQL query'}), 500
    timeSigJSON = response.json()
    time_sig_list = [item['signature']['value'] for item in
                 timeSigJSON['results']['bindings']]
    #print(time_sig_list)
    # Return the JSON data
    return jsonify(time_sig_list), 200


@app.route('/api/tune_type_list', methods=['GET'])
def getTuneTypeList():
    # Generate the SPARQL query
    sparql_query = get_tune_type_list()
    # Execute the SPARQL query
    response = requests.post(
        BLAZEGRAPH_URL,
        data={
            'query': sparql_query,
            'format': 'json'
        }
    )
    #print(sparql_query)
    #print(response.text)
    # Check the response status
    if response.status_code != 200:
        return jsonify({'error': 'Failed to execute SPARQL query'}), 500
    tuneTypeJSON = response.json()
    tune_type_list = [item['genre']['value'] for item in
                 tuneTypeJSON['results']['bindings']]
    #print(tune_type_list)
    # Return the JSON data
    return jsonify(tune_type_list), 200


@app.route('/api/patterns', methods=['GET'])
def getPatterns():
    # Get the query parameters from the GET request
    query_params = request.args.to_dict()
    # Generate the SPARQL query
    sparql_query = get_most_common_patterns_for_a_tune(query_params['id'],
                                                       query_params['excludeTrivialPatterns'])
    # Execute the SPARQL query
    response = requests.post(
        BLAZEGRAPH_URL,
        data={
            'query': sparql_query,
            'format': 'json'
        }
    )

    #print(sparql_query)
    #print(response.text)
    # Check the response status
    if response.status_code != 200:
        return jsonify({'error': 'Failed to execute SPARQL query'}), 500
    # Return the JSON data
    return jsonify(response.json()), 200


@app.route('/api/common_patterns', methods=['GET'])
def getCommonPatterns():
    # Get the query parameters from the GET request
    query_params = request.args.to_dict()
    # Generate the SPARQL query
    sparql_query = get_patterns_in_common_between_two_tunes(query_params['id'],
                                                            query_params['prev'],
                                                            query_params['excludeTrivialPatterns'])
    # Execute the SPARQL query
    response = requests.post(
        BLAZEGRAPH_URL,
        data={
            'query': sparql_query,
            'format': 'json'
        }
    )
    # Check the response status
    if response.status_code != 200:
        return jsonify({'error': 'Failed to execute SPARQL query'}), 500
    # Return the JSON data
    return jsonify(response.json()), 200


@app.route('/api/neighbour_patterns', methods=['GET'])
def getNeighbourPatterns():
    # Get the query parameters from the GET request
    query_params = request.args.to_dict()
    # Generate the SPARQL query
    #print(query_params)
    sparql_query = get_neighbour_patterns_by_tune(query_params['id'],
                                                  query_params['click_num'],
                                                  query_params['excludeTrivialPatterns'])
    # Execute the SPARQL query
    response = requests.post(
        BLAZEGRAPH_URL,
        data={
            'query': sparql_query,
            'format': 'json'
        }
    )
    #print(sparql_query)
    #print(response.text)
    # Check the response status
    if response.status_code != 200:
        return jsonify({'error': 'Failed to execute SPARQL query'}), 500
    # Return the JSON data
    return jsonify(response.json()), 200


@app.route('/api/neighbour_tunes', methods=['GET'])
def getNeighbourTunes():
    # Get the query parameters from the GET request
    query_params = request.args.to_dict()
    # Generate the SPARQL query
    #print(query_params)
    sparql_query = get_neighbour_tunes_by_pattern(query_params['id'],
                                                  query_params['click_num'],)
    # Execute the SPARQL query
    response = requests.post(
        BLAZEGRAPH_URL,
        data={
            'query': sparql_query,
            'format': 'json'
        }
    )
    #print(sparql_query)
    #print(response.text)
    # Check the response status
    if response.status_code != 200:
        return jsonify({'error': 'Failed to execute SPARQL query'}), 500
    # Return the JSON data
    return jsonify(response.json()), 200


@app.route('/api/neighbour_tunes_by_common_patterns', methods=['GET'])
def getNeighbourTunesByCommonPatterns():
    # Get the query parameters from the GET request
    query_params = request.args.to_dict()
    # Generate the SPARQL query
    #print(query_params)
    sparql_query = get_neighbour_tunes_by_common_patterns(query_params['id'],
                                                  query_params['click_num'],)
    # Execute the SPARQL query
    response = requests.post(
        BLAZEGRAPH_URL,
        data={
            'query': sparql_query,
            'format': 'json'
        }
    )
    #print(sparql_query)
    #print(response.text)
    # Check the response status
    if response.status_code != 200:
        return jsonify({'error': 'Failed to execute SPARQL query'}), 500
    # Return the JSON data
    return jsonify(response.json()), 200


@app.route('/api/tune_by_id', methods=['GET'])
def getTuneData():
    # Get the query parameters from the GET request
    query_params = request.args.to_dict()
    # Generate the SPARQL query
    #print(query_params)
    sparql_query = get_tune_data(query_params['id'])
    # Execute the SPARQL query
    response = requests.post(
        BLAZEGRAPH_URL,
        data={
            'query': sparql_query,
            'format': 'json'
        }
    )

    #print(sparql_query)
    #print(response.text)
    # Check the response status
    if response.status_code != 200:
        return jsonify({'error': 'Failed to execute SPARQL query'}), 500
    # Return the JSON data
    return jsonify(response.json()), 200


@app.route('/api/tuneFamilyMembers', methods=['GET'])
def getTuneFamilyMembers():
    # Get the query parameters from the GET request
    query_params = request.args.to_dict()
    # Generate the SPARQL query
    #print(query_params)
    sparql_query = get_tune_family_members(query_params['family'])
    # Execute the SPARQL query
    response = requests.post(
        BLAZEGRAPH_URL,
        data={
            'query': sparql_query,
            'format': 'json'
        }
    )
    #print(sparql_query)
    #print(response.text)
    # Check the response status
    if response.status_code != 200:
        return jsonify({'error': 'Failed to execute SPARQL query'}), 500
    # Return the JSON data
    return jsonify(response.json()), 200


@app.route('/api/tunes_by_pattern', methods=['GET'])
def getTunesContainingPattern():
    # Get the query parameters from the GET request
    query_params = request.args.to_dict()
    # Generate the SPARQL query
    #print(query_params)
    sparql_query = get_pattern_search_query(query_params['pattern'])
    # Execute the SPARQL query
    response = requests.post(
        BLAZEGRAPH_URL,
        data={
            'query': sparql_query,
            'format': 'json'
        }
    )
    #print(sparql_query)
    #print(response.text)
    # Check the response status
    if response.status_code != 200:
        return jsonify({'error': 'Failed to execute SPARQL query'}), 500
    # Return the JSON data
    return jsonify(response.json()), 200


@app.route('/api/kg_version', methods=['GET'])
def getKGVersion():
    # Generate the SPARQL query
    sparql_query = get_kg_version()
    # Execute the SPARQL query
    response = requests.post(
        BLAZEGRAPH_URL,
        data={
            'query': sparql_query,
            'format': 'json'
        }
    )
    #print(sparql_query)
    #print(response.text)
    # Check the response status
    if response.status_code != 200:
        return jsonify({'error': 'Failed to execute SPARQL query'}), 500
    # Return the JSON data
    return jsonify(response.json()), 200


if __name__ == "__main__":
    app.run()
    #app.run(debug=True, port=8000)
    #app.run(host='0.0.0.0', port=443)
    #app.run(host='0.0.0.0', port=5000)
