# dialign_python

This repository has the multi-party version of [dialign](https://github.com/GuillaumeDD/dialign) (Dubuisson Duplessis et al., 2021) implemented in Python. The extension to multi-party dialogues is accepted to AIED 2025 (Asano et al., 2025).

## Notice
This software reimplements and extends [dialign](https://github.com/GuillaumeDD/dialign), which is distributed under the CeCILL-B license.
This reimplementation was developed independently and includes additional features.

The CeCILL-B license text is included in this repository as required.

## Framework
![image](https://github.com/user-attachments/assets/4fd2bca5-2859-4893-8d28-7c087e608ad8)


Our proposed measure extends the notion of shared expressions (Dubuisson Duplessis et al., 2017,2021) to multi-party dialogues. We re-define *shared expressions* as "a surface text pattern inside an utterance that has been produced by **all** speakers, **regardless of to whom they spoke**. An expression can either be
free or constrained, the same as Duplessis et al. (2017); an expression is *free* when it appears in an utterance without being a subexpression of a larger expression, whereas an expression is *constrained* if it appears in a turn as a subexpression of a larger expression (e.g., "two" in "two over three" in the table above). In our definition, a shared expression is *established* when it has been produced by all speakers and at least once in a free form.

Duplessis et al. (2017) define the *initiator* of an expression as, "the interlocutor that first produced an instance of the expression." Similarly, we define the *establisher* as the last interlocutor that produced an instance of the expression, i.e., the interlocutor that established the shared expression in their turn. Note that the acts of initiation and establishment do not have any constraints on the number of turns.

`dialign_python` offers self-repetitions, too (Dubuisson Duplessis et al., 2021). "Self-repetitions are lexical patterns appearing at least twice in the dialogue utterances of a given \[speaker\], independently of the other \[speakers'\] utterances."

### Metrics provided by `dialign_python`
The following explanations are taken from [dialign](https://github.com/GuillaumeDD/dialign) (Dubuisson Duplessis et al. (2021), Asano et al. (2022), and Asano et al. (2025)).
`dialign_python` provides a set of measures to characterise both:
1. the interactive verbal alignment process between dialogue participants, and
2. the self-repetition behaviour of each participant.

These measures allow the characterisation of the nature of these processes by addressing 
various informative aspects such as their variety, strength, complexity, stability, and 
orientation. In a nutshell:
- **variety**: the variety of shared expressions or self-repetitions emerging during a dialogue 
               relative to its length. It is directly related to the number of unique 
               expressions in a lexicon. 
- **strength**: the strength of repetition of the (shared) lexical patterns, i.e., how much the
                patterns are reused.
- **complexity**: the complexity indicates the variety of the types of lexical patterns. It is here 
                  featured by Shannon entropy measures. High entropy indicates the presence of
                  a wide range of lexical patterns relative to their lengths in number of tokens (e.g., ranging 
                  from a single word to a full sentence). On the contrary, low entropy indicates the predominance 
                  of one type of lexical pattern.
- **extension** and **stability**: the extension and stability of the (shared) lexical patterns are related 
                                   to the size of the lexical patterns. The extension indicates the size of the 
                                   lexical patterns. The longer it is, the more extended the lexical pattern is. 
                                   Extension is directly linked to the stability of the processes since the 
                                   more extended the patterns are, the more stable the processes are.
- **orientation**: the orientation of the interactive alignment process, i.e., it indicates either a symmetry 
                   (both dialogue participants initiate and reuse the same number of shared lexical patterns),
                   or an asymmetry (a dialogue participant initiates and/or reuses more shared lexical patterns).
- **activeness**: the activeness of speakers in the establishment of shared lexical patterns.

#### Speaker-independent
| Measure | Description |  Aspects |
| :---:   | :---       |  :---:   |
|  EV     |  Expression Variety (EV). The shared expression lexicon size normalized by the length of the dialogue (which is its total number of tokens in the dialogue).  | Variety | 
|  ER     |  Expression Repetition (ER). The proportion of tokens which speakers dedicate to the repetition of a shared expression.  | Strength |
| ENTR    | Shannon entropy of the lengths in token of the shared expression instances. | Complexity |
| L       | Average length in token of the shared expression instances. | Stability |
| LMAX    | Maximum length in token of the shared expression instances. | Stability |
| EE      | Expression Establishment (EE). The proportion of tokens which speakers dedicate to the establishment of a shared expression. | Activeness |

#### Speaker-dependent

| Measure | Description |  Aspects |
| :---:   | :---       |  :---:   |
|  IE_S     |  Initiated Expression (IE) for locutor S. Ratio of shared expressions initiated by locutor S.   | Orientation | 
|  ER_S     |  Expression Repetition (ER) for locutor S. Ratio of tokens produced by S belonging to an instance of a shared expression.  | Strength |
|  EE_S     |  Expression Establishment (EE) for locutor S. Ratio of tokens produced by S used to establish a new shared expression.  | Activeness |
|  EsE_S    |  Established Expression (EsE) for locutor S. Ratio of shared expressions established by locutor S.   | Orientation |

### Measures Characterising Self-Repetition Behaviour of each Dialogue Participant
| Measure | Description |  Aspects |
| :---:   | :---       |  :---:   |
|  SEV_S  |  Self-Expression Variety (SEV) for locutor S. For locutor S, the self-repetition lexicon size normalized by the total number of tokens produced by S in the dialogue.  | Variety | 
|  SER_S     |  Self-Expression Repetition (SER) for locutor S. The proportion of tokens which locutor S dedicates to self-repetition.| Strength |
| SENTR_S    |  Shannon entropy of the length in token of the self-repetitions from S. | Complexity |
| SL_S       |  Average length in tokens of the self-repetitions from S. | Stability |
| SLMAX_S    |  Maximum length in token of the self-repetitions from S. | Stability |

### Synthetic Presentation of the Provided Measures
| Aspect      | Speaker-independent Measures (*) | Speaker-dependent Measures (**) |
| :---:       | :---:                            | :---:                           |
| Variety     | EV                               |  SEV_S                          | 
| Strength    | ER                               |  ER_S, SER_S                    |
| Complexity  | ENTR                             |  SENTR_S                        |
| Stability   | L, LMAX                          |  SL_S, SLMAX_S                  |
| Orientation |  --                              |  IE_S, EsE_S                    |
| Activeness  | EE                               |  EE_S                           |

(*) All these measures are related to the interactive verbal alignment process

(**) Measures starting with 'S' are related to the self-repetition behaviour, the others
     are related to the interactivate verbal alignment process

### Example
We explain the calculation of our measure using the table above. There are 15 shared expressions: "so," "we," "and," "to," "the," "i," "you," "of," "battery," "it," "one," "two," "you're," "'re," and "two over three" ("'re" and punctuations are counted as one word after tokenization. However, punctuations themselves cannot be shared expressions (Dubuisson Duplessis et al., 2021).). Nine of them are initiated by Emma (a teachable robot), four are initiated by Student A, and two are initiated by Student B. Therefore, $IE_{Emma} = \frac{9}{15}$, $IE_{Student A} = \frac{4}{15}$, and $IE_{Student B} = \frac{2}{15}$. If we group students A and B, $IE_{Student} = \frac{6}{15}$. Similarly, three are established by Emma, seven are established by Student A, and five are established by Student B, so $EsE_{Emma} = \frac{3}{15}$, $EsE_{Student A} = \frac{7}{15}$, and $EsE_{Student B} = \frac{5}{15}$. Emma spoke 114 words, three words were used for the establishment, and 23 were in existing or new expressions. Thus, $ER_{Emma} = \frac{23}{114}$ and $EE_{Emma} = \frac{3}{114}$.


## Installation
After cloning this repo, go to the top directory of the repo and run the following command:
```
python -m pip install .
```
If you do not have your own tokenizer (i.e., you want to use [our default tokenizer](https://github.com/akonoroshi/dialign_python/blob/47af424ee43ad580d01c2d1e5a28e3575954ac6b/dialign_python/utils.py#L6)), run the following command, too:
```
python -m spacy download en_core_web_sm
```

## Usage
There are two modes: offline and online. The offline mode is designed for the analysis of completed dialogues (in other words, you should have transcripts of finished dialogues). The online mode is designed for ongoing dialogues. The online mode can score new utterances using the dialogue history and update the history in real-time.

### Offline mode
```python
from dialign_python.dialign_python_offline import dialign

input_file = "sample_offline_input.csv"
speaker_col = "Speaker"
message_col = "Utterance"
timestamp_col = "Timestamp"
valid_speakers = ["Emma", "Student A", "Student B"]
filters = {'Receiver': valid_speakers}
time_format="%H:%M:%S.%f"

speaker_independent, speaker_dependent, shared_expressions, self_repetitions, online_metrics = dialign(input_file, speaker_col, message_col, timestamp_col, valid_speakers, filters=filters, time_format=time_format)
```
The outputs are
```python
speaker_independent = {'ER': 0.21140939597315436, 'SER': 0.2214765100671141, 'EE': 0.0738255033557047, 'Total tokens': 298, 'Num. shared expressions': 19, 'EV': 0.06375838926174497, 'ENTR': 0.40945861869508926, 'L': 1.1578947368421053, 'LMAX': 3}
speaker_dependent = {'Emma': {'ER': 0.22807017543859648, 'EE': 0.03508771929824561, 'Total tokens': 114, 'Initiated': 0.5789473684210527, 'Established': 0.21052631578947367}
                      'Student A': {'ER': 0.1388888888888889, 'EE': 0.09722222222222222, 'Total tokens': 72, 'Initiated': 0.2631578947368421, 'Established': 0.3684210526315789}
                      'Student B': {'ER': 0.24107142857142858, 'EE': 0.09821428571428571, 'Total tokens': 112, 'Initiated': 0.15789473684210525, 'Established': 0.42105263157894735}}
shared_expressions = [
{'of': {'initiator': 'Emma', 'establisher': 'Student A', 'establishmemt turn': 2, 'turns': [1, 2, 7, 9]},
'we': {'initiator': 'Emma', 'establisher': 'Student A', 'establishmemt turn': 2, 'turns': [1, 2, 0, 4, 5, 7, 9]},
'i': {'initiator': 'Emma', 'establisher': 'Student A', 'establishmemt turn': 2, 'turns': [1, 2, 0, 5, 7, 9]},
'the': {'initiator': 'Emma', 'establisher': 'Student A', 'establishmemt turn': 2, 'turns': [1, 2, 7, 0, 8]},
'and': {'initiator': 'Emma', 'establisher': 'Student A', 'establishmemt turn': 4, 'turns': [1, 4, 0, 8]},
'to': {'initiator': 'Emma', 'establisher': 'Student B', 'establishmemt turn': 5, 'turns': [2, 5, 0, 6, 8, 9]},
'so': {'initiator': 'Emma', 'establisher': 'Student A', 'establishmemt turn': 6, 'turns': [1, 6, 7, 0, 8, 9]},
'you': {'initiator': 'Emma', 'establisher': 'Student A', 'establishmemt turn': 6, 'turns': [5, 6, 7, 0, 8]},
'what': {'initiator': 'Student B', 'establisher': 'Emma', 'establishmemt turn': 7, 'turns': [2, 7, 1, 9]},
'it': {'initiator': 'Student B', 'establisher': 'Emma', 'establishmemt turn': 7, 'turns': [2, 7, 5, 1, 9]},
'one': {'initiator': 'Student B', 'establisher': 'Emma', 'establishmemt turn': 7, 'turns': [4, 7, 6, 8, 1, 9]},
'battery': {'initiator': 'Emma', 'establisher': 'Student B', 'establishmemt turn': 8, 'turns': [6, 8, 7]},
'time': {'initiator': 'Emma', 'establisher': 'Student B', 'establishmemt turn': 8, 'turns': [6, 8]},
'over': {'initiator': 'Emma', 'establisher': 'Student B', 'establishmemt turn': 8, 'turns': [6, 8, 7]},
"you \'re": {'initiator': 'Student A', 'establisher': 'Student B', 'establishmemt turn': 8, 'turns': [7, 8]},
'two': {'initiator': 'Student A', 'establisher': 'Student B', 'establishmemt turn': 8, 'turns': [7, 8, 4, 9, 6]},
'by': {'initiator': 'Student A', 'establisher': 'Student B', 'establishmemt turn': 8, 'turns': [7, 8]},
'two over three': {'initiator': 'Student A', 'establisher': 'Student B', 'establishmemt turn': 8, 'turns': [7, 8]},
"'re": {'initiator': 'Student A', 'establisher': 'Emma', 'establishmemt turn': 9, 'turns': [8, 9]}}]
self_repetitions = {'Emma': {'SER': 0.32456140350877194, 'SEV': 0.19298245614035087, 'SENTR': 0.6631794532105497, 'SL': 1.3636363636363635, 'SLMAX': 5}
                    'Student A': {'SER': 0.1111111111111111, 'SEV': 0.08333333333333333, 'SENTR': 0.8675632284814612, 'SL': 1.5, 'SLMAX': 3}
                    'Student B': {'SER': 0.1875, 'SEV': 0.125, 'SENTR': 0.0, 'SL': 1.0, 'SLMAX': 1}}
online_metrics = [
 {'DEE': 0.0,
  'DER': 0.0,
  'DSER': 0.0,
  'Established Expression': [],
  'Message': 'so now we know how much paint and food to get at the store . but '
             ', before i go to the store , can you help me figure out how much '
             'of my battery i will use over time ?',
  'Repeated Expression': [],
  'Self Repetition': [],
  'Speaker': 'Emma'},
 {'DEE': 0.0,
  'DER': 0.0,
  'DSER': 0.0,
  'Established Expression': [],
  'Message': 'um so if we think about it in terms of minutes , the first one '
             'would be forty minutes and then sixty minutes and then one '
             "eighty . but i do n't know what ratio that would be .",
  'Repeated Expression': [],
  'Self Repetition': [],
  'Speaker': 'Student B'},
 {'DEE': 0.13793103448275862,
  'DER': 0.1724137931034483,
  'DSER': 0.0,
  'Established Expression': ['of', 'we', 'i', 'the'],
  'Message': "i mean she 's kind of a calculator we could always , i 'd ask "
             'her to see what the ratio , yeah , like to simplify it .',
  'Repeated Expression': ['the', 'of', 'we', 'i'],
  'Self Repetition': [],
  'Speaker': 'Student A'},
 {'DEE': 0.0,
  'DER': 0.0,
  'DSER': 0.0,
  'Established Expression': [],
  'Message': 'yeah .',
  'Repeated Expression': [],
  'Self Repetition': [],
  'Speaker': 'Student B'},
 {'DEE': 0.09090909090909091,
  'DER': 0.18181818181818182,
  'DSER': 0.09090909090909091,
  'Established Expression': ['and'],
  'Message': 'should we say divide one hundred and twenty by two ?',
  'Repeated Expression': ['and', 'we'],
  'Self Repetition': ['we'],
  'Speaker': 'Student A'},
 {'DEE': 0.045454545454545456,
  'DER': 0.13636363636363635,
  'DSER': 0.36363636363636365,
  'Established Expression': ['to'],
  'Message': "do you think she can do that ? i mean it does n't hurt to try . "
             'yeah , we can .',
  'Repeated Expression': ['we', 'to', 'i'],
  'Self Repetition': ['do', 'we', 'it', 'think', "n't", 'that', 'yeah'],
  'Speaker': 'Student B'},
 {'DEE': 0.0625,
  'DER': 0.09375,
  'DSER': 0.21875,
  'Established Expression': ['so', 'you'],
  'Message': "so emma , first , you 're gon na try to see how much battery "
             'usage goes into time by dividing one over twenty by two over '
             'three in step zero .',
  'Repeated Expression': ['you', 'to', 'so'],
  'Self Repetition': ['to see', 'to', 'one', 'twenty by two', 'by'],
  'Speaker': 'Student A'},
 {'DEE': 0.07692307692307693,
  'DER': 0.3333333333333333,
  'DSER': 0.3076923076923077,
  'Established Expression': ['what', 'it', 'one'],
  'Message': "i think i understand what you 're saying . so we have two over "
             'three because we have two thirds of an hour for one twentieth of '
             'the battery . student a. do we multiply it by something ?',
  'Repeated Expression': ['of',
                          'you',
                          'so',
                          'one',
                          'we',
                          'what',
                          'it',
                          'i',
                          'the'],
  'Self Repetition': ['of', 'battery', 'you', 'so', 'we', 'i', 'over', 'the'],
  'Speaker': 'Emma'},
 {'DEE': 0.20408163265306123,
  'DER': 0.4897959183673469,
  'DSER': 0.2653061224489796,
  'Established Expression': ['two over three',
                             "you 're",
                             'battery',
                             'time',
                             'over',
                             'two',
                             'by'],
  'Message': "okay . so emma , first , you 're going to take the battery usage "
             ', which is one over twenty and divide that by the time , which '
             "is two over three . so you 're gon na do one over twenty divided "
             'by two over three .',
  'Repeated Expression': ['time',
                          'battery',
                          "you 're",
                          'you',
                          'so',
                          'one',
                          'two',
                          'and',
                          'by',
                          'over',
                          'to',
                          'two over three',
                          'the'],
  'Self Repetition': ['first', 'so', 'one', 'and', 'the', 'you', 'to'],
  'Speaker': 'Student B'},
 {'DEE': 0.029411764705882353,
  'DER': 0.38235294117647056,
  'DSER': 0.7352941176470589,
  'Established Expression': ["'re"],
  'Message': "i get it . so we 're trying to figure out what times two thirds "
             "of an hour will give us one hour . but then i 'm not sure what "
             'to do .',
  'Repeated Expression': ['of',
                          'one',
                          'so',
                          'two',
                          "'re",
                          'we',
                          'what',
                          'it',
                          'i',
                          'to'],
  'Self Repetition': ['figure out',
                      '. but',
                      'will',
                      'get',
                      'to',
                      '. so we',
                      'do',
                      'hour',
                      'one',
                      "'re",
                      'two',
                      'it',
                      'what',
                      'two thirds of an hour'],
  'Speaker': 'Emma'}]
```


### Online mode
For online mode, you can start an infinite loop and then add or score utterances based on the menu options. Here is a sample code for online mode:
```python
from dialign_python.dialign_python_online import Conversation

conversation = Conversation()
while True:
    mode = input("Enter option (a, s, q, w) ")
    if mode == 'q':
        break
    else:
        speaker = input("Enter speaker: ")
        message = input("Enter message: ")
        conversation.request(mode, speaker, message, 1)
```
* a: Add a new message from a speaker.
* s: Add a new message from a speaker and score the utterance for DER and DSER.
* q: Quit the online mode
* w: Update the window size of the conversation context for DER and DSER calculations. 

Here is a sample run of the above code:
```
Enter option (a, s, q, w) a
Enter speaker: Emma
Enter message: Hello human

Conversation history:
('2025-02-25 22:27:10', 'emma', 'Hello human')
Enter option (a, s, q, w) a
Enter speaker: Human
Enter message: Hello Emma

Conversation history:
('2025-02-25 22:27:10', 'emma', 'Hello human')
('2025-02-25 22:27:21', 'human', 'Hello Emma')
Enter option (a, s, q, w) s
Enter speaker: Emma
Enter message: Hello again! How are you?
{'Hello': ['emma', 2, 1]}
Shared Expressions : ['Hello']
{'Hello': ['emma', 3, 1]}
DER: 0.2
DSER: 0.2
DEE: 0.0

Conversation history:
('2025-02-25 22:27:10', 'emma', 'Hello human')
('2025-02-25 22:27:21', 'human', 'Hello Emma')
('2025-02-25 22:27:38', 'emma', 'Hello again! How are you?')
Enter option (a, s, q, w) q
```
The conversation output for online mode will be saved in a conversation_output.tsv file with timestamp, speaker, and the message as tab separated values.

A sample conversation_output.tsv file looks like:
```
2025-02-25 22:27:10	emma	Hello human
2025-02-25 22:27:21	human	Hello Emma
2025-02-25 22:27:38	emma	Hello again! How are you?
```

## Contributing to dialign_python
We always welcome your contributions! Feel free to fork and make a pull request.

## Citing dialign_python
If you use this software or refer to this framework in the context of multi-party interactions (three or more speakers), cite both of the following:
- Asano, Y; Litman, D.; Sharma, P.; Fritsch, D.; King-Shepard, Q.; Nokes-Malach, T.; Kovashka, A.; & Walker, E. Multi-party Lexical Alignment in Collaborative Learning with a Teachable Robot. In Proceedings of the 26th International Conference on Artificial Intelligence in Education, 2025.
- Dubuisson Duplessis, G.; Langlet, C.; Clavel, C.; Landragin, F. Towards alignment strategies in human-agent interactions based on measures of lexical repetitions, Lang Resources & Evaluation, 2021, 36p. https://dx.doi.org/10.1007/s10579-021-09532-w

If you just refer to the framework only in the context of one-on-one human-agent interactions, cite only the latter.

## Acknowledgement
This work was supported by Grant No. 2024645 from the National Science Foundation, Grant No. 220020483 from the James S. McDonnell Foundation, and a University of Pittsburgh Learning Research and Development Center award.

## References
- Asano, Y; Litman, D.; Sharma, P.; Fritsch, D.; King-Shepard, Q.; Nokes-Malach, T.; Kovashka, A.; & Walker, E. Multi-party Lexical Alignment in Collaborative Learning with a Teachable Robot. In Proceedings of the 26th International Conference on Artificial Intelligence in Education, 2025.
- Asano, Y.; Litman, D.; Yu, M.; Lobczowski, N.; Nokes-Malach, T.; Kovashka, A.; & Walker, E. Comparison of Lexical Alignment with a Teachable Robot in Human-Robot and Human-Human-Robot Interactions. In Proceedings of the 23rd Annual Meeting of the Special Interest Group on Discourse and Dialogue, 2022 pp. 615-622. https://aclanthology.org/2022.sigdial-1.57/
- Dubuisson Duplessis, G.; Langlet, C.; Clavel, C.; Landragin, F. Towards alignment strategies in human-agent interactions based on measures of lexical repetitions, Lang Resources & Evaluation, 2021, 36p. https://dx.doi.org/10.1007/s10579-021-09532-w
- Dubuisson Duplessis, G.; Clavel, C.; Landragin, F. Automatic Measures to Characterise Verbal Alignment in Human-Agent Interaction, 18th Annual Meeting of the Special Interest Group on Discourse and Dialogue (SIGDIAL), 2017, pp. 71--81. https://aclanthology.org/W17-5510/
