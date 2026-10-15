# EAS 510 - Assignment 1: Digital Forensics Apprentice

A rule-based expert system that matches modified images back to their originals.

This is the **starter repository** for Project 1. Two repositories matter:

| Repository | Role |
|------------|------|
| `delveccj/EAS510_Assignment1_starter` (this repo) | Your **code** lives here. You will fork it, work in your fork, and push your final submission here. |
| `delveccj/EAS510_Assignment1` | The **dataset** (read-only). Clone it for the images; never commit it to your fork. |

## Setup on your Codio box

```bash
# 1. Fork this repo on GitHub, then in your box:
git clone https://github.com/YOUR-USERNAME/EAS510_Assignment1_starter.git
cd EAS510_Assignment1_starter

# 2. Clone the read-only dataset as a sibling folder (images live there):
cd ~/workspace
git clone https://github.com/delveccj/EAS510_Assignment1.git

# 3. Install dependencies:
cd ~/workspace/EAS510_Assignment1_starter
python3 -m pip install -r requirements.txt

# 4. Point this box at YOUR fork (run once):
./setup_git.sh
```

## Repository layout

```
forensics_detective.py   SimpleDetector: register targets + find_best_match
rules.py                 Rule functions (Rule 1: Metadata, Rule 2: Histogram, Rule 3: Template)
test_system.py           Runs the detector over the data folders and writes results_*.txt
scripts/check_output_format.py   Validates a results file against the required format
setup_git.sh, submit.sh  One-time setup + commit/push helper ("backup button")
```

## The task in one paragraph

Implement three interpretable rules (metadata, color histogram, template matching)
that combine into a 0-100 confidence score. Run your system on `modified_images/`
and `random/` and save the full output as `results_v1.txt`. In Phase 2, run on
`hard/`, diagnose a systematic failure, add a **Rule 4**, and save
`results_v1_hard.txt` and `results_v2.txt`. Full instructions are in the Codio guide
and in the assignment PDF in UBLearns.

## Running

```bash
# Phase 1 (easy + random) -> results_v1.txt
python3 test_system.py --modified --random --output results_v1.txt

# Phase 1 on hard cases -> results_v1_hard.txt
python3 test_system.py --hard --output results_v1_hard.txt

# Phase 2 (everything) -> results_v2.txt
python3 test_system.py --modified --hard --random --output results_v2.txt

# Validate any results file against the required format:
python3 scripts/check_output_format.py results_v1.txt
```

The data folders are resolved from a sibling clone of `EAS510_Assignment1`.
If your data is elsewhere, pass `--data-dir /path/to/EAS510_Assignment1`.

## Output format (do not alter)

```
Processing: modified_image_01.jpg
Rule 1 (Metadata): FIRED - Size ratio 0.85 -> 20/30 points
Rule 2 (Histogram): FIRED - Correlation 0.92 -> 25/30 points
Rule 3 (Template): FIRED - Match score 0.76 -> 30/40 points
Final Score: 75/100 -> MATCH to original_03.jpg
```

## Backup doctrine

Your Codio box can be reset at any time. **Your fork on GitHub is the only safe
copy.** After every milestone run `./submit.sh "describe what you did"`. A box
restart never touches GitHub.

## License

Apache 2.0. See `LICENSE`.


## Observed weakness in V1: what failed and why

V3 and v6 were a problem for V1. it resized and compressed 3/10 and crop and resize 5/10. Rule 3 did not fire any v3 or v6 image.
some of the images that i noted were the following:
Original_01__resize_scale75__compress__q30__v3.jpg
Original_00__resize_scale114__compress__q45__v3.jpg
Original_03__crop_keep60__resized__q60__v6.jpg
original_09__crop_keep50__resized__q75__v6.jpg 


## Design decision for V2: what Rule 4 is and why you chose it
convert the images to grayscale and compute canny edges. search multiple template sizes. record the highest normalized edge match score. reweights the original rules to 25/25/40, leaving 10 points for rules 4.
## Effect of the change: accuracy before/after on easy vs hard
easy accuracy went up from 51.7% in v1 to 96.7% in v2.
hard accuracy decreased from 75% to 48.3%.
v2 did better on easy images but worse on hard images. it still failed to match the hard resize and crop plus resize images. Not all improvements came from Rule 4.
## Trade-offs: what new costs or risks did Rule 4 introduce
Rule 4 checks 27 sizes for each image pair so that adds more work.
Giving points to rule 4 meant reducing the points available to rules 1 and 2. some images that passed v1 then failed v2. 
Rule 4 sometimes gave misleading evidence. It gave 10 points to an image even though that image was unrelated. 'randoM_10.JPEG'. The system was rejected because the total score is 32. 
There is times Rule 4 helped but not enough. It gave 10 point to `original_09__crop_keep50__resized__q75__v6.jpg` but the total wwas only 46 so the image was rejected.
