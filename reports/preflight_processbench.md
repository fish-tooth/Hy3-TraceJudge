# ProcessBench Preflight Report

- dataset: Qwen/ProcessBench
- configs: ['default']


## config=default

- splits: ['gsm8k', 'math', 'olympiadbench', 'omnimath']
  - gsm8k: 400 rows
  - math: 1000 rows
  - olympiadbench: 1000 rows
  - omnimath: 1000 rows
- columns: ['id', 'generator', 'problem', 'steps', 'final_answer_correct', 'label']
- features: {"id": "Value(dtype='string', id=None)", "generator": "Value(dtype='string', id=None)", "problem": "Value(dtype='string', id=None)", "steps": "Sequence(feature=Value(dtype='string', id=None), length=-1, id=None)", "final_answer_correct": "Value(dtype='bool', id=None)", "label": "Value(dtype='int64', id=None)"}

- label min/max: -1 / 7
- label distribution: {1: 61, 2: 50, 0: 37, 4: 13, 3: 31, 5: 12, 6: 2, 7: 1, -1: 193}

- steps length min/max/mean: 2 / 16 / 5.21

- final_answer_correct distribution: {False: 200, True: 200}

### first 3 raw examples (config=default)
  - id='gsm8k-0'
    problem="Sue lives in a fun neighborhood.  One weekend, the neighbors decided to play a prank on Sue.  On Friday morning, the neighbors placed 18 pink plastic flamingos out on Sue's front yard.  On Saturday m...
    steps=['To find out how many more pink plastic flamingos were out than white plastic flamingos at noon on Sunday, we can break down the problem into steps. First, on Friday, the neighbors start with 18 pink...
    label=1
    final_answer_correct=False
    source=None
  - id='gsm8k-1'
    problem="Cindy's math and science books weigh 2 pounds each.  Her French book weighs 4 pounds and her English book weighs 3 pounds.  Her history book weighs twice as much as her English book.  If Cindy carrie...
    steps=["To determine the total weight of all Cindy's books, we need to calculate the weight of each book individually and then sum these weights.", 'First, for the math and science books:\n- Each math book ...
    label=1
    final_answer_correct=False
    source=None
  - id='gsm8k-2'
    problem="A company sold 4000 gallons of milk in jars to Mr. Marcellus' store at the cost of $3.5 per gallon. However, Mr. Marcellus later realized 2/5 of the amount of milk he purchased had passed the expiry ...
    steps=["First, let's calculate the total cost of the milk that Mr. Marcellus bought: Cost per gallon = $3.5, Total gallons purchased = 4000. Total cost = Cost per gallon * Total gallons purchased = $3.5 * 4...
    label=1
    final_answer_correct=False
    source=None

## manual review sample (n=20, seed=42)
| id | label | final_answer_correct | source |
|---|---|---|---|
| gsm8k-327 | -1 | True | None |
| gsm8k-57 | 0 | False | None |
| gsm8k-12 | 1 | False | None |
| gsm8k-379 | -1 | True | None |
| gsm8k-140 | 3 | False | None |
| gsm8k-125 | 3 | False | None |
| gsm8k-114 | 1 | False | None |
| gsm8k-71 | 2 | False | None |
| gsm8k-377 | -1 | True | None |
| gsm8k-52 | 3 | False | None |
| gsm8k-346 | -1 | True | None |
| gsm8k-279 | -1 | True | None |
| gsm8k-44 | 0 | False | None |
| gsm8k-302 | -1 | True | None |
| gsm8k-216 | -1 | True | None |
| gsm8k-16 | 4 | False | None |
| gsm8k-15 | 2 | False | None |
| gsm8k-47 | 3 | False | None |
| gsm8k-111 | 1 | False | None |
| gsm8k-119 | 1 | False | None |