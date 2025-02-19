from multiprocessing import Pool

# This file contains the parallel processing logic:

def scoring_task(args):
    """
    Perform scoring for a single utterance in parallel.

    Calls conversation.score_message() for scoring


    """
    conversation, utterance, speaker, scoring_condition = args
    try:
        # Call score_message
        scores = conversation.score_message(speaker, utterance, scoring_condition)
        if isinstance(scores, tuple) and len(scores) == 3:
            der_score, dser_score, dee = scores
            return (utterance, {"DER": der_score, "DSER": dser_score, "DEE": dee})
        else:
            return (utterance, {"DER": None, "DSER": None, "DEE": None})
    except Exception as e:
        print(f"Error scoring utterance: {utterance} | Error: {e}")
        return (utterance, {"DER": "Error", "DSER": "Error", "DEE": "Error"})



def score_utterances_in_parallel(conversation, utterances, speaker, scoring_condition):
    """
    Perform parallel scoring on a list of utterances.

    Uses Pool(processes=4) to create a pool of 4 worker processes

    Distributes the tasks using pool.map, which applies scoring_task to each tuple in parallel
    """
    try:
        print(f"Starting parallel scoring for {len(utterances)} utterances.")
        if speaker not in conversation.persons:
            from dialign_python import Person
            conversation.persons[speaker] = Person(speaker)


        args = [(conversation, utterance, speaker, scoring_condition) for utterance in utterances]

        with Pool(processes=4) as pool:
            results = pool.map(scoring_task, args)
        return results
    except Exception as e:
        print(f"Error during parallel scoring: {e}")
        return []