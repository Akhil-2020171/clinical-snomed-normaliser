# Clinical SNOMED Normaliser

A Clinical NLP service that extracts clinical entities from free-text medical notes, detects their assertion status, links them to SNOMED CT concepts, and produces a normalized representation of the original text.

---

## 1. Project Overview

Clinical notes contain valuable medical information, but the information is usually written as free text.

For example:

> The patient complains of chest pain but has no fever.

A human can understand that:

* `chest pain` is a clinical symptom and is present.
* `fever` is a clinical symptom but is absent.

A computer system cannot reliably perform downstream processing using only the original text.

This project converts the free text into structured clinical information:

```text
Clinical Text
     |
     v
Clinical NER
     |
     +---- SYMPTOM
     +---- DISEASE
     +---- PROCEDURE
     +---- MEDICATION
     |
     v
Assertion Detection
     |
     +---- PRESENT
     +---- ABSENT
     +---- HISTORICAL
     +---- etc.
     |
     v
SNOMED CT Linking
     |
     v
Normalized Clinical Entities
     |
     v
Transformed Text
```

The project is implemented as a Python/FastAPI NLP service and is designed to be consumed by another application/service through an HTTP API.

---

# 2. Motivation

The initial motivation for this project came from the NRCeS resource:

**Webinar on Clinical NLP using SNOMED CT**

The webinar introduced the idea of combining Clinical NLP with SNOMED CT so that information expressed in natural clinical language can be converted into standardized clinical concepts.

NRCeS provides the webinar under its resources section:

* [NRCeS Resources](https://www.nrces.in/resources)

The project uses that general idea as its starting point and implements a local Clinical NLP pipeline.

One of the ideas that particularly influenced this project was the concept of converting the original clinical text into a representation in which identified clinical expressions are replaced with their SNOMED CT identifiers and Fully Specified Names (FSNs).

For example:

```text
The patient complains of chest pain.
```

can become conceptually:

```text
The patient complains of 29857009|Chest pain (finding).
```

This creates a bridge between:

```text
Human-readable clinical text
```

and:

```text
Machine-readable standardized terminology
```

---

# 3. Problem Statement

Clinical text is difficult to process because the same clinical concept can be expressed in many different ways.

Examples:

```text
chest pain
Chest Pain
patient reports chest pain
pain in the chest
```

Similarly, clinical concepts may occur in different contexts:

```text
The patient has fever.
```

versus:

```text
The patient has no fever.
```

versus:

```text
The patient had fever last year.
```

The words alone are not enough.

A useful Clinical NLP system therefore needs to answer several questions:

1. What clinical entity is present?
2. What type of entity is it?
3. Where does it occur in the original text?
4. Is the entity present, absent, or historical?
5. Which standardized SNOMED CT concept represents it?
6. Can the original text be transformed without losing the surrounding clinical context?

This project addresses these problems.

---

# 4. Main Features

The NLP service currently supports:

* Clinical Named Entity Recognition (NER)
* Symptom extraction
* Disease extraction
* Procedure extraction
* Medication extraction
* Assertion detection
* SNOMED CT concept linking
* SNOMED CT hierarchy-aware candidate ranking
* Lexical normalization
* Contained-term fallback matching
* Overlapping entity resolution
* Exact source-text offsets
* SNOMED CT concept replacement in the original text
* REST API using FastAPI
* Local/in-memory SNOMED CT terminology loading
* Docker-based deployment

---

# 5. High-Level Architecture

```text
                         +----------------------+
                         |      Client/App      |
                         +----------+-----------+
                                    |
                                    | HTTP
                                    v
                         +----------------------+
                         |     FastAPI NLP      |
                         |       Service        |
                         +----------+-----------+
                                    |
                    +---------------+---------------+
                    |               |               |
                    v               v               v
                  NER          Assertion        SNOMED CT
                    |           Detection         Linker
                    |               |               |
                    +---------------+---------------+
                                    |
                                    v
                         Structured NLP Response
                                    |
                                    v
                             transform_text()
                                    |
                                    v
                         Normalized Clinical Text
```

---

# 6. NER Models

The service uses separate models for different clinical entity types.

| Entity     | Model                                                  |
| ---------- | ------------------------------------------------------ |
| SYMPTOM    | `DT4H/en-symptom-cardioberta-multiclass-ner`           |
| DISEASE    | `DT4H/en-disease-cardioberta-multiclass-ner`           |
| PROCEDURE  | `DT4H/cardio-ner-en-procedure-cardioberta-multiclass`  |
| MEDICATION | `DT4H/cardio-ner-en-medication-cardioberta-multiclass` |

The models are loaded using Hugging Face Transformers.

Conceptually:

```text
Clinical text
      |
      +--> Symptom model
      |
      +--> Disease model
      |
      +--> Procedure model
      |
      +--> Medication model
      |
      v
Combined entity list
```

Each entity contains at least:

```json
{
  "mention": "chest pain",
  "start": 25,
  "end": 35,
  "label": "SYMPTOM"
}
```

The `start` and `end` values are character offsets into the original text.

---

# 7. Why Separate NER Models?

Different clinical entity types have different linguistic characteristics.

Instead of relying on one generic model to identify every possible clinical concept, this project uses specialized models for:

```text
Symptoms
Diseases
Procedures
Medications
```

This also allows the SNOMED linker to use the entity type when ranking candidate concepts.

For example:

```text
SYMPTOM
    -> prefer Clinical Finding concepts

DISEASE
    -> prefer Disease / Clinical Finding concepts

PROCEDURE
    -> prefer Procedure concepts

MEDICATION
    -> prefer Substance concepts
```

This entity-aware approach is important because the same lexical expression can potentially correspond to multiple SNOMED CT concepts.

---

# 8. Entity Overlap Handling

Multiple NER models may identify overlapping spans.

For example, different models could identify:

```text
blister
blister on the left hand
```

as entities.

The extractor therefore performs an overlap-resolution step.

The current implementation prefers the longer entity span when entities overlap.

This prevents the final response from containing conflicting overlapping entities.

---

# 9. Assertion Detection

Finding an entity is not enough.

Consider:

```text
The patient has chest pain.
```

and:

```text
The patient has no chest pain.
```

Both contain:

```text
chest pain
```

but their clinical meaning is different.

The assertion detector therefore determines the contextual status of an extracted entity.

Examples:

```text
chest pain
    -> PRESENT

fever
    -> ABSENT

myocardial infarction five years ago
    -> HISTORICAL
```

The assertion detector is deterministic and explainable rather than relying on another machine-learning model.

This makes its behavior easier to inspect and test.

The project includes regression tests covering present, absent, historical, and temporal expressions.

---

# 10. SNOMED CT

## What is SNOMED CT?

SNOMED CT is a clinical terminology designed to represent clinical information using standardized concepts.

A concept has a permanent SNOMED CT identifier.

For example:

```text
29857009
```

represents:

```text
Chest pain (finding)
```

This allows free-text clinical expressions to be connected to a standardized clinical concept.

SNOMED CT describes its terminology as a common language that supports consistent indexing, storage, retrieval, and aggregation of clinical information across specialties and sites of care.

Useful references:

* [SNOMED International](https://www.snomed.org/)
* [SNOMED CT Documentation](https://docs.snomed.org/)
* [SNOMED CT International Edition information](https://www.nlm.nih.gov/healthit/snomedct/international.html)

---

# 11. Why SNOMED CT?

Without terminology normalization:

```text
chest pain
Chest Pain
pain in chest
precordial pain
```

may appear to be different strings to a computer.

After terminology normalization, they can potentially be mapped to the same standardized clinical concept where an appropriate SNOMED CT mapping exists.

This makes the information more useful for:

* Clinical analytics
* Search
* Decision support
* Interoperability
* Data aggregation
* Standardized reporting
* Downstream clinical applications

---

# 12. SNOMED CT International Edition

This project uses the **SNOMED CT International Edition** release files.

The terminology is not stored in a database.

Instead, the application loads the required SNOMED CT release files into memory when the NLP service starts.

The project uses the SNOMED CT **Snapshot** release.

SNOMED International defines a Snapshot as containing the most recent version of each component as of the release date.

The Snapshot is particularly useful when an application needs the current terminology state rather than the historical version of every component.

SNOMED CT uses Release Format 2 (RF2) for its release files.

The standard RF2 representation includes files for components such as:

```text
Concepts
Descriptions
Relationships
Reference Sets
```

References:

* [SNOMED CT Release Schedule and File Formats](https://docs.snomed.org/snomed-ct-practical-guides/snomed-ct-starter-guide/13-release-schedule-and-file-formats)
* [SNOMED CT Release Types](https://docs.snomed.org/snomed-ct-specifications/snomed-ct-release-file-specification/release-types-packages-and-files/3.2-release-types)

---

# 13. Why Use the Snapshot Instead of a Database?

The project intentionally does not use a database for SNOMED CT terminology storage.

Instead:

```text
SNOMED CT Snapshot files
          |
          v
      File loader
          |
          v
  In-memory dictionaries
          |
          v
      SNOMED linker
```

The terminology is loaded into structures optimized for lookup.

This keeps the prototype simple and avoids introducing database infrastructure just for terminology storage.

The trade-off is that the application must load the terminology into memory when the service starts.

For a production implementation, memory usage, startup time, terminology versioning, update strategy, and deployment architecture would need to be evaluated carefully.

---

# 14. SNOMED CT Data Used by the Application

The linker uses terminology information such as:

```text
Concept ID
Fully Specified Name (FSN)
Descriptions / Synonyms
Relationships / Parents
```

The application builds lookup structures such as:

```text
term -> concept IDs

concept ID -> FSN

concept ID -> descriptions

concept ID -> parent concepts
```

This allows the linker to perform both lexical and hierarchy-aware matching.

---

# 15. SNOMED CT Semantic Tags

A SNOMED CT Fully Specified Name contains a semantic tag.

Examples:

```text
Diabetes mellitus (disorder)

Chest pain (finding)
```

The semantic tag is the text inside the final parentheses:

```text
disorder
finding
```

The linker extracts this tag and includes it in the response.

This provides additional information about the selected concept.

---

# 16. SNOMED CT Candidate Ranking

A text expression can potentially have multiple SNOMED CT candidates.

The linker therefore does not simply select the first lexical match.

It considers:

### Lexical match

Examples:

```text
FSN
Synonym
Lexically normalized term
Contained term
```

### Hierarchy

The linker checks whether a candidate belongs to relevant SNOMED CT hierarchies.

Examples:

```text
Clinical finding
Disease
Procedure
Substance
Qualifier value
Body structure
```

### Entity type

The entity type extracted by NER influences candidate selection.

For example:

```text
PROCEDURE
    -> Procedure hierarchy is preferred

MEDICATION
    -> Substance hierarchy is preferred

SYMPTOM
    -> Clinical Finding hierarchy is preferred

DISEASE
    -> Disease hierarchy is preferred
```

This reduces incorrect mappings caused by purely lexical similarity.

---

# 17. Lexical Normalization

Clinical text is not always written exactly like a SNOMED CT description.

The project therefore includes a lexical normalization step.

Basic normalization includes operations such as:

```text
"Chest Pain"
       |
       v
"chest pain"
```

and:

```text
"  chest   pain  "
       |
       v
"chest pain"
```

A controlled lexical normalizer is also used as a fallback when the original expression does not directly match the terminology.

---

# 18. Contained-Term Matching

The linker also has a contained-term fallback.

For example, if an extracted entity contains a longer phrase that does not directly exist in the terminology, the linker can search for SNOMED terms contained within the phrase.

The linker prefers longer matching terms and removes terms that are completely contained inside an already selected longer match.

This is a fallback mechanism and is used only after direct and lexical-normalized matching have been attempted.

---

# 19. Example SNOMED Linking

Input:

```text
The patient has diabetes mellitus and chest pain.
```

Potential normalized concepts:

```text
diabetes mellitus
    ->
73211009 | Diabetes mellitus (disorder)

chest pain
    ->
29857009 | Chest pain (finding)
```

The exact selected concept depends on the terminology release and the linker ranking logic.

---

# 20. End-to-End Example

Input:

```text
The patient complains of chest pain but has no fever.
```

The pipeline identifies:

```text
chest pain
    label: SYMPTOM
    assertion: PRESENT

fever
    label: SYMPTOM
    assertion: ABSENT
```

The SNOMED linker can then associate:

```text
chest pain
    ->
29857009 | Chest pain (finding)

fever
    ->
386661006 | Fever (finding)
```

The API response contains the extracted entities together with their assertions and SNOMED information.

---

# 21. Transforming the Original Text

The project also provides `transform_text()`.

The purpose is to preserve the original sentence while replacing linked clinical expressions with their SNOMED representation.

Conceptually:

```text
Original:

The patient complains of chest pain but has no fever.
```

becomes:

```text
The patient complains of
29857009|Chest pain (finding)
but has no
386661006|Fever (finding).
```

The replacement uses the original character offsets.

Replacements are applied from the end of the text toward the beginning.

This is important because replacing text from left to right would change the character positions of later entities.

---

# 22. Why Keep the Original Text?

The transformed text is not intended to replace the original clinical note.

The original text remains important because it is:

* Human-readable
* Clinically interpretable
* Auditable
* Useful for debugging

The transformed representation provides an additional normalized representation for downstream processing.

Therefore the system can retain both:

```text
Original clinical text
```

and:

```text
SNOMED-normalized text
```

---

# 23. Project Structure

A simplified project structure is:

```text
clinical-snomed-normaliser/
│
├── nlp-service/
│   │
│   ├── app/
│   │   ├── ner/
│   │   ├── linker/
│   │   ├── preprocessing/
│   │   ├── schemas/
│   │   └── main.py
│   │
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .venv/
│
├── docker-compose.yml
│
└── README.md
```

The exact structure may evolve as the Java API service is integrated.

---

# 24. NLP Service Components

### `app/main.py`

The FastAPI application entry point.

It initializes:

```text
AssertionDetector
ClinicalNerModels
ClinicalEntityExtractor
SnomedLoader
SnomedLinker
```

and exposes the extraction API.

### `app/ner/`

Contains the NER model loading and entity extraction logic.

### `app/linker/`

Contains:

```text
SNOMED terminology loading
SNOMED candidate lookup
Lexical normalization
Hierarchy traversal
Candidate ranking
```

### `app/schemas/`

Contains request and response schemas used by the API.

---

# 25. Python Environment

The NLP service can be run directly using a Python virtual environment.

## Linux / macOS

From the `nlp-service` directory:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Make the snomed files accessible:

```bash
export SNOMED_HOST_PATH=/home/sub-escanor/Public/Data/SNOMEDCT/International-Edition
```

Run the service:

```bash
uvicorn app.main:app --reload
```

For a non-development run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

# 26. Windows PowerShell

From the `nlp-service` directory:

```powershell
python -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Make the snomed files accessible:

```powershell
$env:SNOMED_BASE="C:\SNOMEDCT\International-Edition\Snapshot\Terminology"
```

Run the service:

```powershell
uvicorn app.main:app --reload
```

For network/container-style access:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If PowerShell blocks script execution, the local Python environment may require an appropriate execution-policy configuration on the developer machine.

---

# 27. Running Without Docker

Linux/macOS:

```bash
cd nlp-service

source .venv/bin/activate

pip install -r requirements.txt

export SNOMED_HOST_PATH=/home/sub-escanor/Public/Data/SNOMEDCT/International-Edition

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Windows PowerShell:

```powershell
cd nlp-service

.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

$env:SNOMED_HOST_PATH="C:\SNOMEDCT\International-Edition"

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API should then be available at:

```text
http://localhost:8000
```

FastAPI's interactive API documentation is available at:

```text
http://localhost:8000/docs
```

---

# 28. Docker

Docker provides a reproducible environment for running the NLP service without requiring every developer to manually configure Python, PyTorch, Transformers, and the other dependencies.

The NLP service contains its own Dockerfile.

The root project contains:

```text
docker-compose.yml
```

which can be used to start the application stack.

---

# 29. Docker Build

From the project root:

```bash
docker build -t clinical-snomed-nlp ./nlp-service
```

Run:

```bash
docker run --rm \
  -p 8000:8000 \
  clinical-snomed-nlp
```

The service will then be available at:

```text
http://localhost:8000
```

---

# 30. Docker Compose

From the project root:

```bash
docker compose up --build
```

To run in the background:

```bash
docker compose up --build -d
```

To stop the services:

```bash
docker compose down
```

To view logs:

```bash
docker compose logs -f
```

If only the NLP service is being demonstrated:

```bash
docker compose up --build nlp-service
```

---

# 31. SNOMED CT Data and Docker

SNOMED CT release files should not be downloaded automatically by the Docker build unless the organization has explicitly decided to distribute them that way and the appropriate licensing/distribution requirements have been addressed.

Instead, the terminology release can be supplied to the application as a mounted directory/volume.

Conceptually:

```text
Host
│
└── SNOMEDCT/
       │
       └── International-Edition/
              │
              └── Snapshot/
```

The container receives this directory through a Docker volume.

This keeps the terminology release separate from the application image.

It also makes it easier to update the terminology release without rebuilding the application image.

SNOMED International distributes release packages through its licensing and distribution mechanisms, and licensing requirements should be checked for the intended deployment and territory.

---

# 32. Why the SNOMED Release Is Kept Outside the Image

The SNOMED CT release is terminology data, not application source code.

Keeping it outside the image provides several advantages:

```text
Application image
        +
SNOMED CT release
        =
Running service
```

A new terminology release can therefore be introduced without rebuilding the Python application image.

For example:

```text
September 2026 Snapshot
          |
          v
     current setup

Future Snapshot
          |
          v
replace mounted terminology data
```

The application can then be restarted using the new release.

---

# 33. API

The primary endpoint is:

```text
POST /extract
```

Example request:

```json
{
  "text": "The patient complains of chest pain but has no fever."
}
```

The response contains the extracted clinical entities and their associated processing information.

A typical entity contains information such as:

```json
{
  "mention": "chest pain",
  "start": 25,
  "end": 35,
  "label": "SYMPTOM",
  "assertion": "PRESENT",
  "snomed": [
    {
      "conceptId": "29857009",
      "fsn": "Chest pain (finding)"
    }
  ]
}
```

The exact response schema should be treated as the source of truth in `app/schemas/`.

---

# 34. Testing

Testing should cover the individual stages as well as the complete pipeline.

Important test categories include:

### NER

```text
SYMPTOM
DISEASE
PROCEDURE
MEDICATION
```

### Assertions

```text
PRESENT
ABSENT
HISTORICAL
```

including temporal expressions such as:

```text
five years ago
3 months ago
two weeks ago
```

### SNOMED linking

Test:

```text
Exact term
Synonym
Lexical normalization
Contained term
Multiple candidates
Incorrect hierarchy
```

### Offset handling

Verify that:

```text
start
end
mention
```

always correspond to the original input text.

### Transformation

Verify that multiple SNOMED replacements do not corrupt the original text.

---

# 35. Important Design Decisions

## No SNOMED database

The project deliberately does not introduce a database for SNOMED CT.

Terminology is loaded from the local release files into memory.

## Entity-specific NER

Separate NER models are used for different clinical entity categories.

## Entity-aware SNOMED ranking

SNOMED candidates are ranked using both lexical similarity and terminology hierarchy information.

## Deterministic assertion detection

Assertion detection is rule-based and explainable.

## Preserve source offsets

Every entity retains its position in the original text.

## Preserve original text

The normalized representation is generated in addition to the original clinical text.

---

# 36. What We Learned

This project involved several important lessons about Clinical NLP.

### 36.1 NER alone is not enough

Detecting:

```text
chest pain
```

does not tell us whether the patient currently has chest pain.

Context is required.

---

### 36.2 Generic medical NER models are not necessarily sufficient

A model can recognize that a phrase is medically relevant while still producing a label that is not useful for the application's intended ontology.

For this project, we needed explicit categories:

```text
SYMPTOM
DISEASE
PROCEDURE
MEDICATION
```

---

### 36.3 NER and terminology linking are different problems

NER answers:

> What span of text is clinically relevant?

SNOMED linking answers:

> Which standardized clinical concept represents this span?

These should not be treated as the same task.

---

### 36.4 Exact lexical matching is not enough

A term can have:

* synonyms
* different casing
* whitespace differences
* lexical variations
* multiple SNOMED concepts

Therefore the linker needs normalization and candidate ranking.

---

### 36.5 SNOMED hierarchy information is useful

Pure string matching can return technically valid but clinically inappropriate candidates.

Hierarchy information provides an additional signal.

For example:

```text
PROCEDURE
    -> Procedure hierarchy

MEDICATION
    -> Substance hierarchy
```

This makes the entity type extracted by NER useful during terminology linking.

---

### 36.6 Character offsets are important

Offsets allow the system to connect the extracted entity back to the exact original text.

They are also required for reliable text transformation.

---

### 36.7 Replacement order matters

If text is replaced from left to right, earlier replacements can change the offsets of later entities.

Therefore replacements are applied from the highest starting offset toward the lowest.

---

### 36.8 Snapshot releases simplify terminology consumption

For this application we are interested primarily in the current terminology state rather than the complete history of every SNOMED component.

The Snapshot release is therefore a natural fit for this type of lookup-oriented application.

---

### 36.9 Standardized terminology creates interoperability potential

Free text is optimized for human communication.

SNOMED CT identifiers are optimized for standardized representation.

The NLP pipeline provides a bridge between the two.

---

# 37. Limitations

This project is a prototype/working implementation and should not be considered a complete clinical decision-support system.

Potential limitations include:

* NER model errors
* False positives
* False negatives
* Assertion detection limitations
* Ambiguous clinical terminology
* Incomplete SNOMED mappings
* Terminology release differences
* Memory consumption when loading SNOMED CT
* Model startup time
* English-language dependency of the current models
* Limited context understanding for complex clinical narratives

Clinical text should therefore not be assumed to be perfectly normalized.

---

# 38. Future Improvements

Possible future improvements include:

* More clinical entity categories
* Better medication normalization
* More advanced assertion/context detection
* Negation scope detection
* Temporal relation extraction
* Family-history detection
* Experiencer detection
* More sophisticated terminology ranking
* Improved handling of abbreviations
* Better handling of spelling variation
* Terminology version management
* Performance optimization
* Model caching
* Batch processing
* Production monitoring
* Authentication and authorization
* API gateway integration
* FHIR integration

---

# 39. Important Terminology

### Clinical NLP

Natural Language Processing applied to clinical/medical text.

### NER

Named Entity Recognition.

Identifies meaningful spans of text and assigns entity labels.

### Assertion

The contextual status of a clinical entity.

Examples:

```text
PRESENT
ABSENT
HISTORICAL
```

### SNOMED CT

A standardized clinical terminology containing concepts, descriptions, relationships, and reference sets.

### Concept ID

The unique SNOMED CT identifier of a concept.

### FSN

Fully Specified Name.

The unambiguous official name of a SNOMED CT concept.

Example:

```text
Chest pain (finding)
```

### Semantic Tag

The semantic category at the end of an FSN.

Example:

```text
Chest pain (finding)
            ^^^^^^^
```

### RF2

Release Format 2, the standard format used for SNOMED CT release files.

### Snapshot

A SNOMED CT release containing the latest version of each component at the release date.

### Terminology Linking

Mapping a clinical text expression to a standardized terminology concept.

---

# 40. Quick Start

## Option A — Docker

From the project root:

```bash
docker compose up --build
```

Then open:

```text
http://localhost:8000/docs
```

---

## Option B — Linux/macOS

```bash
cd nlp-service

python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Option C — Windows PowerShell

```powershell
cd nlp-service

python -m venv .venv

.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

# 41. Demonstration Example

Use the following example during a project demonstration:

```text
The patient complains of chest pain but has no fever.
```

Explain the processing as:

```text
1. NER identifies:
       chest pain -> SYMPTOM
       fever      -> SYMPTOM

2. Assertion detection identifies:
       chest pain -> PRESENT
       fever      -> ABSENT

3. SNOMED linking identifies:
       chest pain -> 29857009 | Chest pain (finding)
       fever      -> 386661006 | Fever (finding)

4. transform_text() produces a normalized representation.
```

This demonstrates the complete journey:

```text
Free text
   ↓
Entity recognition
   ↓
Clinical context
   ↓
Standard terminology
   ↓
Normalized text
```

---

# 42. References

### NRCeS

National Resource Centre for EHR Standards:

https://www.nrces.in/

### NRCeS Resources

https://www.nrces.in/resources

### Clinical NLP using SNOMED CT

Available through the NRCeS resources under Webinars.

### SNOMED International

https://www.snomed.org/

### SNOMED CT Documentation

https://docs.snomed.org/

### SNOMED CT Release Formats

https://docs.snomed.org/snomed-ct-practical-guides/snomed-ct-starter-guide/13-release-schedule-and-file-formats

### SNOMED CT International Edition

https://www.nlm.nih.gov/healthit/snomedct/international.html

---

# 43. License and SNOMED CT Notice

This project's source code and SNOMED CT terminology data should be treated separately.

SNOMED CT is distributed under licensing arrangements managed by SNOMED International and its relevant national/member distribution mechanisms.

The SNOMED CT release files used by this project should not automatically be committed to a public source-code repository.

Before deploying or distributing a system containing SNOMED CT, verify the applicable licensing and usage requirements for the organization and territory.

See:

https://www.snomed.org/licensing

---

# 44. Project Status

Current NLP pipeline:

```text
[✓] Clinical NER
[✓] Symptom extraction
[✓] Disease extraction
[✓] Procedure extraction
[✓] Medication extraction
[✓] Assertion detection
[✓] SNOMED CT terminology loading
[✓] SNOMED CT linking
[✓] Hierarchy-aware candidate ranking
[✓] Lexical normalization
[✓] Contained-term fallback
[✓] Overlap resolution
[✓] Text transformation
[✓] FastAPI endpoint
[ ] Final Docker packaging
[ ] Final Docker Compose integration
[ ] Full application integration
```

The NLP service is considered feature-complete for the current project scope. The remaining work is primarily packaging, reproducibility, integration, and production hardening.
