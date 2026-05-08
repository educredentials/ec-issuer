---
name: ADR editor
description: 
  Use this skill to read, write and update Architecture Decision Records, ADRs
  Keywords: ADR, documentation
---

# Reading ADRs

ADRs are located in the ADR directory. ADR diretory can be found in the AGENT.md of the project.
Other common locations to look, are ./docs/adrs?, ./docs/adr, docs/src/adrs, etc.

ADRs have the number and title in their filename. The numbers follow order. 
ADRs may be superceded, in which case the ADR is no longer valid and replaced by another one. The one replacing it should be linked from the now deprecated ADR, but will also be linked to, from the ADR that supercedes the now-deprecated one.

## Writing ADRs

### Process

1. **Gather requirements** 
   - ask user about:
    - What exact decision are we recording?
    - What is the problem we must solve?
    - Why must we decide on this?
    - Any reference materials to include?
   - gather alternatives:
    - What other options are there?
    - Is one solution obviously superior or must we research them further
    - Give a summarized list of pros and cons for each alternative

2. **Draft the ADR** 
  - Look up current highest ADR number
  - Decide on a name
  - Create a new file in the ADR directory
  - new ADR with proper metadata, like current name, status, author, etc.
  - add summary, problem statement and possible solutions
  - add alternatives considered with their pros and cons

3. **Review with user** - present draft and ask:
   - Does this cover your decision?
   - Did we cover all alternatives and options?
   - Anything missing or unclear?
   - Should any section be more/less detailed?
   - Must we further drill down on the alternatives?

### Integrate

Add the new ADR to the docs, by linkin it in ./docs/src/SUMMARY.md

## Guidelines

DO:
* Write concise and clear
* Give concrete examples
* Always check URLS you add, check if they are valid and point to the expected resource.
* Write it as draft.

DON't:
* Put a status to accepted unless explicitly instructed by the user
* Introduce new terminology that does not already appear in other ADRs or the project wide GLOSSARY. Check AGENT.md for the location of the Glossary

## Updating ADRs

ADRs can be updated untill they are "final". 

Updating "follows" exact the rules and context form Writing.

In addition, when updating, check the Template for additional fields or chapters that may be added.

A "final" ADR can only be changed if it is superceded by another ADR, in which
case the only changes are the change of the status to "superceded" and a link to
the new ADR.

## Template

```
---
# These are optional elements. Feel free to remove any of them.
status: {proposed | rejected | accepted | deprecated | … | superseded by [ADR-0005](0005-example.md)}
date: {YYYY-MM-DD when the decision was last updated}
deciders: {list everyone involved in the decision}
consulted: {list everyone whose opinions are sought (typically subject-matter experts); and with whom there is a two-way communication}
informed: {list everyone who is kept up-to-date on progress; and with whom there is a one-way communication}
---
# {short title of solved problem and solution}

## Context and Problem Statement

{Describe the context and problem statement, e.g., in free form using two to three sentences or in the form of an illustrative story.
 You may want to articulate the problem in form of a question and add links to collaboration boards or issue management systems.}

<!-- This is an optional element. Feel free to remove. -->
## Decision Drivers

* {decision driver 1, e.g., a force, facing concern, …}
* {decision driver 2, e.g., a force, facing concern, …}
* … <!-- numbers of drivers can vary -->

## Considered Options

* {title of option 1}
* {title of option 2}
* {title of option 3}
* … <!-- numbers of options can vary -->

## Decision Outcome

Chosen option: "{title of option 1}", because
{justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | … | comes out best (see below)}.

<!-- This is an optional element. Feel free to remove. -->
### Consequences

* Good, because {positive consequence, e.g., improvement of one or more desired qualities, …}
* Bad, because {negative consequence, e.g., compromising one or more desired qualities, …}
* … <!-- numbers of consequences can vary -->

<!-- This is an optional element. Feel free to remove. -->
## Validation

{describe how the implementation of/compliance with the ADR is validated. E.g., by a review or an ArchUnit test}

<!-- This is an optional element. Feel free to remove. -->
## Pros and Cons of the Options

### {title of option 1}

<!-- This is an optional element. Feel free to remove. -->
{example | description | pointer to more information | …}

* Good, because {argument a}
* Good, because {argument b}
<!-- use "neutral" if the given argument weights neither for good nor bad -->
* Neutral, because {argument c}
* Bad, because {argument d}
* … <!-- numbers of pros and cons can vary -->

### {title of other option}

{example | description | pointer to more information | …}

* Good, because {argument a}
* Good, because {argument b}
* Neutral, because {argument c}
* Bad, because {argument d}
* …

<!-- This is an optional element. Feel free to remove. -->
## More Information

{You might want to provide additional evidence/confidence for the decision outcome here and/or
 document the team agreement on the decision and/or
 define when this decision when and how the decision should be realized and if/when it should be re-visited and/or
 how the decision is validated.
 Links to other decisions and resources might here appear as well.}
```
