import requests

NUM_NODES = 5


# A search for tunes containing a given pattern.
def get_pattern_search_query(pattern):
    sparql_query = """PREFIX jams:<http://w3id.org/polifonia/ontology/jams/>
                        PREFIX mm:<http://w3id.org/polifonia/ontology/music-meta/>
                        PREFIX core:<http://w3id.org/polifonia/ontology/core/>
                        PREFIX xyz:<http://sparql.xyz/facade-x/data/>
                        PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                        SELECT DISTINCT ?tune_name ?tuneType ?key ?signature ?id
                        WHERE
                        {
	                        ?obs jams:ofPattern ?patternURI.
	                        ?patternURI xyz:pattern_content \"""" + pattern + """\".
                            ?annotation jams:includesObservation ?obs.
                            ?annotation jams:isJAMSAnnotationOf ?musicalComposition.
                            ?musicalComposition rdf:type mm:MusicEntity.
                            ?musicalComposition core:id ?id.
                            OPTIONAL {?musicalComposition core:title ?tune_name}
                            OPTIONAL {?musicalComposition mm:hasFormType ?tuneTypeURI.
                               ?tuneTypeURI core:name ?tuneType.}
                            OPTIONAL {?musicalComposition mm:hasKey ?keyURI.
                               ?keyURI mm:tuneKeyName ?key.}
                            OPTIONAL {?musicalComposition jams:timeSignature ?signatureURI.
                               ?signatureURI mm:timesig ?signature.}
                        } ORDER BY ?tune_name ?id"""
    return sparql_query


# Return a list of the most frequent patterns in a tune.
def get_most_common_patterns_for_a_tune(id, excludeTrivialPatterns):
    sparql_query = """PREFIX jams:<http://w3id.org/polifonia/ontology/jams/>
                        PREFIX core:<http://w3id.org/polifonia/ontology/core/>
                        PREFIX xyz:<http://sparql.xyz/facade-x/data/>
                        PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                        PREFIX mm:<http://w3id.org/polifonia/ontology/music-meta/>

                        SELECT ?pattern (count(?pattern) as ?patternFreq)
                        WHERE {
                            ?tune rdf:type mm:MusicEntity.
                            ?tune core:id \"""" + id + """\".
                            ?xx jams:isJAMSAnnotationOf ?tune.
                            ?xx jams:includesObservation ?observation.
                            ?observation jams:ofPattern ?patternURI.
                        """
    if excludeTrivialPatterns == "true":
        sparql_query += """ ?patternURI xyz:pattern_complexity ?comp.
                            FILTER (?comp > "0.4"^^xsd:float).
                        """
    sparql_query += """?patternURI xyz:pattern_content ?pattern.
                        } group by ?pattern
                        order by DESC (?patternFreq) LIMIT 10"""
    return sparql_query


# Return a list of patterns contained in two tunes.
def get_patterns_in_common_between_two_tunes(id, prev):
    sparql_query = """PREFIX jams:<http://w3id.org/polifonia/ontology/jams/>
                        PREFIX core:  <http://w3id.org/polifonia/ontology/core/>
                        PREFIX xyz:  <http://sparql.xyz/facade-x/data/>
                        PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                        PREFIX mm:<http://w3id.org/polifonia/ontology/music-meta/>
                        SELECT ?pattern
                        {
                            ?tune1 rdf:type mm:MusicEntity.
                            ?tune1 core:id \"""" + id + """\".
                            ?xx1 jams:isJAMSAnnotationOf ?tune1.
                            ?xx1 jams:includesObservation ?observation1 .
                            ?observation1 jams:ofPattern ?patternURI .
                            ?tune2 rdf:type mm:MusicEntity.
                            ?tune2 core:id \"""" + prev + """\".
                            ?xx2 jams:isJAMSAnnotationOf ?tune2.
                            ?xx2 jams:includesObservation ?observation2 .
                            ?observation2 jams:ofPattern ?patternURI .
                            ?patternURI xyz:pattern_content ?pattern .
                        } group by ?pattern
                        order by DESC (count(?pattern)) ?pattern LIMIT 10"""
    return sparql_query


# A fuzzy search of tune titles.
def get_tune_given_name(matched_ids):
    sparql_query =   """PREFIX jams:<http://w3id.org/polifonia/ontology/jams/>
                        PREFIX mm: <http://w3id.org/polifonia/ontology/music-meta/>
                        PREFIX core:  <http://w3id.org/polifonia/ontology/core/>
                        PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                        SELECT ?tune_name ?tuneType ?key ?signature ?id
                        {
                            ?tune rdf:type mm:MusicEntity.
                            ?tune core:title ?tune_name.
                            ?tune core:id ?id.
                            OPTIONAL {?tune mm:hasFormType ?tuneTypeURI.
                               ?tuneTypeURI core:name ?tuneType.}
                            OPTIONAL {?tune mm:hasKey ?keyURI.
                               ?keyURI mm:tuneKeyName ?key.}
                            OPTIONAL {?tune jams:timeSignature ?signatureURI.
                               ?signatureURI mm:timesig ?signature.}
                            VALUES (?title ?match_strength ?id) { ( \""""
    sparql_query += "\" ) ( \"".join(['\" \"'.join(map(str,tup)) for tup in matched_ids])
    sparql_query += "\" ) }\n} ORDER BY DESC(xsd:integer(?match_strength)) ?title ?id LIMIT 200"
    return sparql_query


# Advanced search.
def advanced_search(query_params, matched_ids):
    sparql_query = """PREFIX jams:<http://w3id.org/polifonia/ontology/jams/>
                        PREFIX mm:<http://w3id.org/polifonia/ontology/music-meta/>
                        PREFIX ttype:<http://w3id.org/polifonia/resource/tunetype>
                        PREFIX key:<http://w3id.org/polifonia/resource/key>
                        PREFIX tsig:<http://w3id.org/polifonia/resource/timeSignature>
                        PREFIX prov:<http://www.w3.org/ns/prov#>
                        PREFIX core:<http://w3id.org/polifonia/ontology/core/>
                        PREFIX xyz:<http://sparql.xyz/facade-x/data/>
                        PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                        SELECT DISTINCT ?tune_name ?tuneType ?key ?signature ?id
                        WHERE
                        {
                            ?tune rdf:type mm:MusicEntity.\n
                        """

    if query_params['pattern'][0]:
        sparql_query +=     "?patternURI xyz:pattern_content \"" + query_params['pattern'][0] + """\".
                            ?obs jams:ofPattern ?patternURI.
                            ?annotation jams:includesObservation ?obs.
                            ?annotation jams:isJAMSAnnotationOf ?tune.
                            """

    if 'corpus' in query_params:
        sparql_query +=     """?tune core:isMemberOf ?corpusURI .
                            ?corpusURI core:isDefinedBy <http://w3id.org/polifonia/resource/tunes/CollectionConcept/ElectronicCollection>.
                            ?corpusURI core:name ?corpus.
                            VALUES (?corpus) { ( \""""
        sparql_query += "\" ) ( \"".join(query_params['corpus'])
        sparql_query += "\" ) }\n"

    if 'tuneType' in query_params:
        sparql_query +=     """?tune mm:hasFormType ?tuneTypeURI .\n
                            ?tuneTypeURI core:name ?tuneType .\n 
                            VALUES (?tuneType) { ( \""""
        sparql_query += "\" ) ( \"".join(query_params['tuneType'])
        sparql_query += "\" ) }\n"
    else:
        sparql_query +=     """OPTIONAL {?tune mm:hasFormType ?tuneTypeURI.\n
                                  ?tuneTypeURI core:name ?tuneType.}\n"""

    if 'key' in query_params:
        sparql_query +=     """?tune mm:hasKey ?keyURI .\n
                            ?keyURI mm:tuneKeyName ?key.\n
                            VALUES (?key) { ( \""""
        sparql_query += "\" ) ( \"".join(query_params['key'])
        sparql_query += "\" ) }\n"
    else:
        sparql_query +=     """OPTIONAL {?tune mm:hasKey ?keyURI.\n
                                  ?keyURI mm:tuneKeyName ?key.}\n"""

    if 'timeSignature' in query_params:
        sparql_query +=     """?tune jams:timeSignature ?timeSignatureURI .\n
                            ?timeSignatureURI mm:timesig ?signature.\n
                            VALUES (?signature) { ( \""""
        sparql_query += "\" ) ( \"".join(query_params['timeSignature'])
        sparql_query += "\" ) }\n"
    else:
        sparql_query += """OPTIONAL {?tune jams:timeSignature ?signatureURI.\n
                              ?signatureURI mm:timesig ?signature.}\n"""

    if query_params['title'][0]:
        sparql_query +=  """?tune core:title ?tune_name .\n
                            VALUES(?title ?match_strength ?id) {( \""""
        sparql_query += "\" ) ( \"".join(['\" \"'.join(map(str,tup)) for tup in matched_ids])
        sparql_query += "\" ) }\n"
    else:
        sparql_query += "   OPTIONAL {?tune core:title ?tune_name}\n"

    sparql_query +=     "?tune core:id ?id.}"
    if query_params['title'][0]:
        sparql_query += " ORDER BY DESC(xsd:integer(?match_strength)) ?title ?id LIMIT 200"
    else:
        sparql_query += " ORDER BY ?tune_name ?id LIMIT 200"
    return sparql_query


# Return a list of all tune names for use by the fuzzy search algorithm.
def get_all_tune_names():
    sparql_query =   """PREFIX core:<http://w3id.org/polifonia/ontology/core/>
                        PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                        PREFIX mm:<http://w3id.org/polifonia/ontology/music-meta/>
                        SELECT DISTINCT ?title ?id
                        {
                            ?tune rdf:type mm:MusicEntity.
                            ?tune core:title ?title.
                            ?tune core:id ?id.
                        }
                     """
    return sparql_query


# Get the pattern node data for the tune-pattern network visualisation.
def get_neighbour_patterns_by_tune(id, click_num, excludeTrivialPatterns):
    offset = NUM_NODES*int(click_num)
    sparql_query =   """PREFIX jams:<http://w3id.org/polifonia/ontology/jams/>
                        PREFIX mm:<http://w3id.org/polifonia/ontology/music-meta/>
                        PREFIX core:<http://w3id.org/polifonia/ontology/core/>
                        PREFIX xyz:<http://sparql.xyz/facade-x/data/>
                        PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                        SELECT ?pattern (count(?pattern) as ?patternFreq)
                        {
                            ?tune rdf:type mm:MusicEntity.
                            ?tune core:id \"""" + id + """\".
                            ?xx jams:isJAMSAnnotationOf ?tune.
                            ?xx jams:includesObservation ?observation .
                            ?observation jams:ofPattern ?patternURI .
                            ?patternURI xyz:pattern_complexity ?comp.
                        """
    if excludeTrivialPatterns == "true":
        sparql_query += """FILTER (?comp > "0.4"^^xsd:float) .
                        """
    sparql_query +=     """?patternURI xyz:pattern_content ?pattern.
                        } group by ?pattern order by ?comp DESC (?patternFreq)
                        OFFSET """ + str(offset) + " LIMIT " + str(NUM_NODES)
    return sparql_query


# Get the tune node data for the tune-pattern network visualisation.
def get_neighbour_tunes_by_pattern(pattern, click_num):
    offset = NUM_NODES*int(click_num)
    sparql_query =       """PREFIX jams:<http://w3id.org/polifonia/ontology/jams/>
                            PREFIX mm:<http://w3id.org/polifonia/ontology/music-meta/>
                            PREFIX core:  <http://w3id.org/polifonia/ontology/core/>
                            PREFIX xyz:<http://sparql.xyz/facade-x/data/>
                            PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                            PREFIX tunes:<http://w3id.org/polifonia/ontology/tunes/>
                            SELECT DISTINCT ?title ?id ?family
                            WHERE
                            {
                                ?patternURI xyz:pattern_content \"""" + pattern + """\".
                                ?obs jams:ofPattern ?patternURI.
                                ?annotation jams:includesObservation ?obs.
                                ?annotation jams:isJAMSAnnotationOf ?tune.
                                ?tune rdf:type mm:MusicEntity.
                                ?tune core:id ?id.
                                ?tune core:isMemberOf ?tuneFamilyURI.
                                ?tuneFamilyURI rdf:type tunes:TuneFamily.
                                ?tuneFamilyURI mm:tuneFamilyName ?family.
                                OPTIONAL {?tune core:title ?title}
                            }  ORDER BY ?title ?id
                            OFFSET """ + str(offset) + " LIMIT " + str(NUM_NODES)
    return sparql_query


# Get tune data when composition page loads.
def get_tune_data(id):
    sparql_query =   """PREFIX mm:<http://w3id.org/polifonia/ontology/music-meta/>
                        PREFIX core:<http://w3id.org/polifonia/ontology/core/>
                        PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                        PREFIX tunes:<http://w3id.org/polifonia/ontology/tunes/>
                        SELECT ?title ?tuneFamily ?link
                        WHERE {
                            ?tune rdf:type mm:MusicEntity.
                            ?tune core:id \"""" + id + """\".
                            ?tune core:title ?title.
                            OPTIONAL{?tune core:isMemberOf ?tuneFamilyURI.
                            ?tuneFamilyURI rdf:type tunes:TuneFamily.
                            ?tuneFamilyURI mm:tuneFamilyName ?tuneFamily.}
                            OPTIONAL{?tune core:description ?link.}
                        }"""
    return sparql_query


# Get a list of member tunes of a given tune family for display on the tune family page.
def get_tune_family_members(family):
    sparql_query =       """PREFIX mm:<http://w3id.org/polifonia/ontology/music-meta/>
                            PREFIX core:  <http://w3id.org/polifonia/ontology/core/>
                            PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                            PREFIX tunes:<http://w3id.org/polifonia/ontology/tunes/>
                            SELECT DISTINCT ?title ?id ?type
                            WHERE
                            {
                                ?tune rdf:type mm:MusicEntity.
                                ?tune core:isMemberOf ?tuneFamilyURI.
                                ?tuneFamilyURI rdf:type tunes:TuneFamily.
                                ?tuneFamilyURI mm:tuneFamilyName \""""+ family +"""\".
                                OPTIONAL {?tune core:title ?title}
                                ?tune core:id ?id.
                                OPTIONAL {?tune mm:hasFormType ?typeURI.
                                    ?typeURI core:name ?type.}
                            } ORDER BY ASC (?title)"""
    return sparql_query


# Get the tune node data for the tune-tune network visualisation.
def get_neighbour_tunes_by_common_patterns(id, click_num):
    offset = NUM_NODES*int(click_num)
    sparql_query =       """PREFIX jams:<http://w3id.org/polifonia/ontology/jams/>
                            PREFIX mm:<http://w3id.org/polifonia/ontology/music-meta/>
                            PREFIX core:<http://w3id.org/polifonia/ontology/core/>
                            PREFIX xyz:<http://sparql.xyz/facade-x/data/>
                            PREFIX tunes:<http://w3id.org/polifonia/ontology/tunes/>
                            PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                            SELECT DISTINCT ?title ?id ?family
                            WHERE
                            {
                                ?givenTune rdf:type mm:MusicEntity.
                                ?givenTune core:id \"""" + id + """\".
                                ?givenTune core:id ?givenTuneId.
                                ?givenAnnot jams:isJAMSAnnotationOf ?givenTune.
                                ?givenAnnot jams:includesObservation ?givenObs.
                                ?givenObs jams:ofPattern ?patternURI.
                                ?otherObs jams:ofPattern ?patternURI.
                                ?otherAnnot jams:includesObservation ?otherObs.
                                ?otherAnnot jams:isJAMSAnnotationOf ?otherTune.
                                ?otherTune rdf:type mm:MusicEntity.
                                ?otherTune core:id ?id.
                                FILTER(?id != ?givenTuneId).
                                ?otherTune core:title ?title.
                                OPTIONAL{?otherTune core:isMemberOf ?tuneFamilyURI.
                                ?tuneFamilyURI rdf:type tunes:TuneFamily.
                                ?tuneFamilyURI mm:tuneFamilyName ?family.}
                                ?patternURI xyz:pattern_content ?pattern.
                                ?patternURI xyz:pattern_complexity ?complexity.
                            }  ORDER BY DESC(?complexity)
                            OFFSET """ + str(offset) + " LIMIT " + str(NUM_NODES)
    return sparql_query


# Return a list of all corpus values to populate the advanced search drop-down.
def get_corpus_list():
    sparql_query =   """PREFIX core:<http://w3id.org/polifonia/ontology/core/>
                        PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                        PREFIX mm:<http://w3id.org/polifonia/ontology/music-meta/>
                        SELECT DISTINCT ?corpus
                        WHERE
                        {
                            ?tune rdf:type mm:MusicEntity.
                            ?tune core:isMemberOf ?corpusURI.
                            ?corpusURI core:isDefinedBy <http://w3id.org/polifonia/resource/tunes/CollectionConcept/ElectronicCollection>.
                            ?corpusURI core:name ?corpus.
                        } ORDER BY ?corpus"""
    return sparql_query


# Return a list of all key values to populate the advanced search drop-down.
def get_keys_list():
    sparql_query =   """PREFIX jams:<http://w3id.org/polifonia/ontology/jams/>
                        PREFIX mm:<http://w3id.org/polifonia/ontology/music-meta/>
                        SELECT DISTINCT ?key
                        WHERE
                        {
                            ?keyURI mm:tuneKeyName ?key.
                        } ORDER BY ?key"""
    return sparql_query


# Return a list of all time signature values to populate the advanced search drop-down.
def get_time_sig_list():
    sparql_query =   """PREFIX mm:<http://w3id.org/polifonia/ontology/music-meta/>
                        SELECT DISTINCT ?signature
                        WHERE
                        {
                            ?timesigURI mm:timesig ?signature.
                        } ORDER BY ?signature"""
    return sparql_query


# Return a list of all tune type values to populate the advanced search drop-down.
def get_tune_type_list():
    sparql_query =   """PREFIX mm:<http://w3id.org/polifonia/ontology/music-meta/>
                        PREFIX core:<http://w3id.org/polifonia/ontology/core/>
                        SELECT DISTINCT ?tuneType
                        WHERE
                        {
                            ?tune rdf:type mm:MusicEntity.
                            ?tune mm:hasFormType ?tuneTypeURI.
                            ?tuneTypeURI core:name ?tuneType.
                        } ORDER BY ?tuneType"""
    return sparql_query


# Return the release version of the knowledge graph.
# Is there a risk of multiple results?
def get_kg_version():
    sparql_query =   """PREFIX jams:<http://w3id.org/polifonia/ontology/jams/>
                        SELECT DISTINCT ?version
                        WHERE
                        {
                            ?s jams:release ?version
                        }"""
    return sparql_query


if __name__ == "__main__":
    # Generate the SPARQL query
    sparql_query = get_tune_given_name("Yankee Doodle")
    # Execute the SPARQL query
    response = requests.post(
        BLAZEGRAPH_URL,
        data={
            'query': sparql_query,
            'format': 'json'
        }
    )
    # Return the JSON data
    data = response.json()
    print(data)
