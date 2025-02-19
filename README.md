# dialign_python

This repository has the multi-party version of [dialign](https://github.com/GuillaumeDD/dialign) (Dubuisson Duplessis et al., 2021) implemented in Python. The extension to multi-party dialogues is under review at AIED 2025 (Anonymous, 2025).

## Framework
![image](https://github.com/user-attachments/assets/54e9cf16-b8ec-4b7a-92d0-e22407e1a19d)

Our proposed measure extends the notion of shared expressions (Dubuisson Duplessis et al., 2021; Duplessis et al., 2017) to multi-party dialogues. We re-define *shared expressions* as "a surface text pattern inside an utterance that has been produced by **all** speakers, **regardless of to whom they spoke**. An expression can either be
free or constrained, the same as Duplessis et al. (2017); an expression is *free* when it appears in an utterance without being a subexpression of a larger expression, whereas an expression is *constrained* if it appears in a turn as a subexpression of a larger expression (e.g., "two" in "two over three" in the table above). In our definition, a shared expression is *established* when it has been produced by all speakers and at least once in a free form.

Duplessis et al. (2017( define the *initiator* of an expression as, "the interlocutor that first produced an instance of the expression." Similarly, we define the *establisher* as the last interlocutor that produced an instance of the expression, i.e., the interlocutor that established the shared expression in their turn. Note that the acts of initiation and establishment do not have any constraints on the number of turns.

### Metrics provided by dialign_python


## Installation
After cloning this repo, go to the top directory of the repo and run the following:
```
python -m pip install .
```

## Usage
There are two modes: offline and online. The offline mode is designed for the analysis of completed dialogues (in other words, you should have transcripts of finished dialogues). The online mode is designed for ongoing dialogues. The online mode can score new utterances using the dialogue history and update the history in real-time.

### Offline mode


### Online mode


## References
- Anonymous, Multi-party Lexical Alignment in Collaborative Learning with a Teachable Robot, under review at 26th International Conference on Artificial Intelligence in Education, 2025.
- Dubuisson Duplessis, G.; Langlet, C.; Clavel, C.; Landragin, F., Towards alignment strategies in human-agent interactions based on measures of lexical repetitions, Lang Resources & Evaluation, 2021, 36p. https://dx.doi.org/10.1007/s10579-021-09532-w
- Dubuisson Duplessis, G.; Clavel, C.; Landragin, F., Automatic Measures to Characterise Verbal Alignment in Human-Agent Interaction, 18th Annual Meeting of the Special Interest Group on Discourse and Dialogue (SIGDIAL), 2017, pp. 71--81. https://aclanthology.org/W17-5510/
