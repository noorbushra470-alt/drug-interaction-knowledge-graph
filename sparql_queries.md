# SPARQL Competency Queries

21 competency questions answered with SPARQL over the drug knowledge graph (named graph `<http://example.org/drugkg/graphs/data>`), grouped by difficulty.

## Easy Competency Questions

### CQ1. Drug profile for DrugBank ID DB00006

**Question:** Print the drug profile of the drug with DrugBank ID DB00006, including its name, description, indication and mechanism of action.

```sparql
PREFIX ex: <http://example.org/drugkg/>
PREFIX drug: <https://go.drugbank.com/drugs/>

SELECT ?name ?description ?indication ?mechanismOfAction
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    drug:DB00006 ex:hasName ?name .
    OPTIONAL { drug:DB00006 ex:hasDescription ?description . }
    OPTIONAL { drug:DB00006 ex:hasIndication ?indication . }
    OPTIONAL { drug:DB00006 ex:hasMechanismOfAction ?mechanismOfAction . }
  }
}
```

**How it works:** The query directly accesses the drug node using its DrugBank URI (DB00006) and retrieves core properties using OPTIONAL clauses to handle missing values.

### CQ2. Approved or investigational drugs

**Question:** Fetch drugs that are assigned to groups "approved" or "investigational".

```sparql
PREFIX ex: <http://example.org/drugkg/>

SELECT DISTINCT ?drug ?name ?group
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    ?drug a ex:Drug ;
          ex:hasGroup ?group .
    OPTIONAL { ?drug ex:hasName ?name . }
    FILTER(?group = "approved" || ?group = "investigational")
  }
}
```

**How it works:** The query matches all Drug nodes that have a hasGroup property and applies a FILTER to retain only approved or investigational groups.

### CQ3. Synonyms of DB00009

**Question:** Fetch all the synonyms of the drug DB00009.

```sparql
PREFIX ex: <http://example.org/drugkg/>
PREFIX drug: <https://go.drugbank.com/drugs/>

SELECT ?synonym
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    drug:DB00009 ex:hasSynonym ?synonym .
  }
}
```

**How it works:** The query directly accesses drug DB00009 and retrieves all hasSynonym property values linked to it.

### CQ4. Unique chemical states for 10 random drugs

**Question:** What are the unique chemical states (e.g., solid, liquid) recorded for 10 random drugs?

```sparql
PREFIX ex: <http://example.org/drugkg/>

SELECT DISTINCT ?drug ?state
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    ?drug a ex:Drug ;
          ex:hasState ?state .
  }
}
LIMIT 10
```

**How it works:** The query matches Drug nodes with a hasState property and uses LIMIT 10 to sample 10 random drugs with their chemical states.

### CQ5. Drugs with molecular weight > 500

**Question:** Which are the names of the drugs that have a molecular weight strictly greater than 500?

```sparql
PREFIX ex: <http://example.org/drugkg/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT ?name ?mw
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    ?drug a ex:Drug ;
          ex:hasName ?name ;
          ex:hasMolecularWeight ?mw .
    FILTER(xsd:float(?mw) > 500)
  }
}
ORDER BY DESC(?mw)
```

**How it works:** The query retrieves all drugs with a hasMolecularWeight property and applies a numeric FILTER to keep only those with molecular weight greater than 500.

### CQ6. Drugs under kingdom "Organic compounds"

**Question:** What are the names of the drugs that are classified under the kingdom "Organic compounds"?

```sparql
PREFIX ex: <http://example.org/drugkg/>

SELECT DISTINCT ?name
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    ?drug a ex:Drug ;
          ex:hasName ?name ;
          ex:hasKingdom ?kingdom .
    FILTER(LCASE(?kingdom) = "organic compounds")
  }
}
```

**How it works:** The query matches Drug nodes with a hasKingdom property and filters for the value Organic compounds using LCASE for case-insensitive matching.

### CQ7. Genes manifesting enzyme proteins for Pegfilgrastim

**Question:** Which genes (names and descriptions) manifest the proteins that act as enzymes for the drug named "Pegfilgrastim"?

```sparql
PREFIX ex: <http://example.org/drugkg/>
PREFIX protein: <https://www.uniprot.org/uniprotkb/>

SELECT DISTINCT ?geneName ?geneDescription
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    ?drug a ex:Drug ;
          ex:hasName "Pegfilgrastim" ;
          ex:hasEnzyme ?enzyme .
    ?enzyme ex:encodedBy ?gene .
    OPTIONAL { ?gene ex:hasName ?geneName . }
    OPTIONAL { ?gene ex:hasGeneDescription ?geneDescription . }
  }
}
```

**How it works:** The query traverses drug → hasEnzyme → enzyme → encodedBy → gene and retrieves gene name and description using OPTIONAL clauses.

### CQ8. Drug label with synonym count

**Question:** List the drug label and the count of its synonyms, ordered from highest to lowest.

```sparql
PREFIX ex: <http://example.org/drugkg/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?name (COUNT(?synonym) AS ?synonymCount)
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    ?drug a ex:Drug ;
          ex:hasName ?name .
    OPTIONAL { ?drug ex:hasSynonym ?synonym . }
  }
}
GROUP BY ?name
ORDER BY DESC(?synonymCount)
```

**How it works:** The query groups drugs by name and counts hasSynonym values per drug using COUNT aggregation, ordered from highest to lowest.

## Moderate Competency Questions

### CQ9. All proteins including missing names

**Question:** List all proteins in the database, their UniProt ID and their names, including those that do not have a recorded name.

```sparql
PREFIX ex: <http://example.org/drugkg/>

SELECT DISTINCT ?protein ?uniprotID ?name
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    ?protein a ex:Protein ;
             ex:hasUniProtID ?uniprotID .
    OPTIONAL { ?protein ex:hasName ?name . }
  }
}
```

**How it works:** The query matches all Protein nodes and retrieves their UniProt ID. Protein name is retrieved using OPTIONAL to include proteins without a recorded name.

### CQ10. Drugs with superclass but no subclass

**Question:** Which drugs belong to a "superclass" but lack a "subclass" in their chemical hierarchy?

```sparql
PREFIX ex: <http://example.org/drugkg/>

SELECT DISTINCT ?drug ?name ?superclass
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    ?drug a ex:Drug ;
          ex:hasName ?name ;
          ex:hasSuperclass ?superclass .
    FILTER NOT EXISTS { ?drug ex:hasSubclass ?subclass . }
  }
}
```

**How it works:** The query matches drugs with a hasSuperclass property and uses FILTER NOT EXISTS to exclude drugs that also have a hasSubclass property.

### CQ11. Proteins targeted by more than 3 drugs

**Question:** Which proteins are acting as targets for more than 3 different drugs and what is the name of the genes that manifest those proteins?

```sparql
PREFIX ex: <http://example.org/drugkg/>

SELECT ?protein ?proteinName ?geneName (COUNT(DISTINCT ?drug) AS ?drugCount)
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    ?drug a ex:Drug ;
          ex:hasTarget ?protein .
    OPTIONAL { ?protein ex:hasName ?proteinName . }
    OPTIONAL {
      ?protein ex:encodedBy ?gene .
      ?gene ex:hasName ?geneName .
    }
  }
}
GROUP BY ?protein ?proteinName ?geneName
HAVING(COUNT(DISTINCT ?drug) > 3)
ORDER BY DESC(?drugCount)
```

**How it works:** The query groups proteins by their drug targets using COUNT, filters for proteins targeted by more than 3 drugs, and retrieves associated gene names via encodedBy.

### CQ12. Unique interacting drug pairs

**Question:** Find all pairs of interacting drugs (by name). Ensure there are no duplicate pairs retrieved (A–B is the same as B–A).

```sparql
PREFIX ex: <http://example.org/drugkg/>

SELECT DISTINCT ?name1 ?name2
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    ?drug1 a ex:Drug ;
           ex:hasName ?name1 ;
           ex:interactsWith ?drug2 .
    ?drug2 a ex:Drug ;
           ex:hasName ?name2 .
    FILTER(STR(?drug1) < STR(?drug2))
  }
}
```

**How it works:** The query retrieves interacting drug pairs using interactsWith and applies FILTER STR(?drug1) < STR(?drug2) to eliminate duplicate symmetric pairs.

### CQ13. Drugs, targets, and actions

**Question:** List all drugs, their target proteins, and the action they have on the target (e.g., inhibitor/activator). If a drug has no known targets, do not include it. If a protein has no name, leave it blank.

```sparql
PREFIX ex: <http://example.org/drugkg/>

SELECT DISTINCT ?drugName ?proteinName ?action
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    ?drug a ex:Drug ;
          ex:hasName ?drugName ;
          ex:hasTarget ?protein .
    OPTIONAL { ?protein ex:hasName ?proteinName . }
    OPTIONAL { ?protein ex:hasAction ?action . }
  }
}
```

**How it works:** The query matches drugs with at least one target via hasTarget, retrieves protein name and action using OPTIONAL to handle missing values.

### CQ14. Average molecular weight by kingdom

**Question:** What is the average molecular weight of drugs within each chemical "kingdom"?

```sparql
PREFIX ex: <http://example.org/drugkg/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?kingdom (AVG(xsd:float(?mw)) AS ?avgMW)
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    ?drug a ex:Drug ;
          ex:hasKingdom ?kingdom ;
          ex:hasMolecularWeight ?mw .
  }
}
GROUP BY ?kingdom
ORDER BY DESC(?avgMW)
```

**How it works:** The query groups drugs by hasKingdom and computes the average molecular weight using AVG aggregation on hasMolecularWeight values.

### CQ15. Sample drugs in pathways involving both a Drug and an Enzyme

**Question:** Find 10 sample drugs (they must be unique) that are involved in pathways that involve both a Drug and an Enzyme.

```sparql
PREFIX ex: <http://example.org/drugkg/>

SELECT DISTINCT ?drugName
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    ?drug a ex:Drug ;
          ex:hasName ?drugName ;
          ex:hasPathway ?pathway .
    ?pathway ex:pathwayHasDrug ?drug .
    ?pathway ex:pathwayHasEnzyme ?enzyme .
  }
}
LIMIT 10
```

**How it works:** The query matches drugs connected to a pathway via hasPathway, then checks the pathway has both pathwayHasDrug and pathwayHasEnzyme links. LIMIT 10 ensures unique sample.

## Challenging Competency Questions

### CQ16. Average molecular weight by full classification path

**Question:** Group all drugs by their full chemical classification path (Kingdom → Superclass → Subclass → Direct Parent) and find the average molecular weight for each unique classification path.

```sparql
PREFIX ex: <http://example.org/drugkg/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?kingdom ?superclass ?subclass ?directParent 
       (AVG(xsd:float(?mw)) AS ?avgMW)
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    ?drug a ex:Drug ;
          ex:hasMolecularWeight ?mw .
    OPTIONAL { ?drug ex:hasKingdom ?kingdom . }
    OPTIONAL { ?drug ex:hasSuperclass ?superclass . }
    OPTIONAL { ?drug ex:hasSubclass ?subclass . }
    OPTIONAL { ?drug ex:hasDirectParent ?directParent . }
  }
}
GROUP BY ?kingdom ?superclass ?subclass ?directParent
ORDER BY DESC(?avgMW)
```

**How it works:** The query uses OPTIONAL for all four classification levels and groups by the full path combination, computing AVG molecular weight per unique classification path.

### CQ17. Target protein interacting with an enzyme for the same drug

**Question:** Find drugs that target a protein, where that specific target protein also interacts with another protein that acts as an enzyme for the same drug.

```sparql
PREFIX ex: <http://example.org/drugkg/>

SELECT DISTINCT ?drugName ?targetName ?enzymeName
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    ?drug a ex:Drug ;
          ex:hasName ?drugName ;
          ex:hasTarget ?target ;
          ex:hasEnzyme ?enzyme .
    ?target ex:interactsWithProtein ?enzyme .
    OPTIONAL { ?target ex:hasName ?targetName . }
    OPTIONAL { ?enzyme ex:hasName ?enzymeName . }
  }
}
```

**How it works:** The query matches drug → hasTarget → target protein, drug → hasEnzyme → enzyme, then checks target interactsWithProtein enzyme to find the multi-hop condition.

### CQ18. Top 3 heaviest drugs with direct parent and optional pathways

**Question:** Find the top 3 heaviest drugs (by molecular weight). For only these 3 drugs, fetch their direct-parent classification and optionally the names of any pathways they are involved in.

```sparql
PREFIX ex: <http://example.org/drugkg/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?drugName ?mw ?directParent ?pathwayName
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    {
      SELECT ?drug ?drugName ?mw
      WHERE {
        ?drug a ex:Drug ;
              ex:hasName ?drugName ;
              ex:hasMolecularWeight ?mw .
      }
      ORDER BY DESC(xsd:float(?mw))
      LIMIT 3
    }
    OPTIONAL { ?drug ex:hasDirectParent ?directParent . }
    OPTIONAL {
      ?drug ex:hasPathway ?pathway .
      ?pathway ex:pathwayName ?pathwayName .
    }
  }
}
```

**How it works:** A subquery ranks drugs by molecular weight and returns top 3. The outer query then retrieves their direct parent classification and optional pathway names.

### CQ19. Genes manifesting enzymes but not targets

**Question:** List the names of genes that manifest enzymes but strictly exclude genes that manifest any protein acting as a drug target.

```sparql
PREFIX ex: <http://example.org/drugkg/>

SELECT DISTINCT ?geneName
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    ?enzyme a ex:Enzyme ;
            ex:encodedBy ?gene .
    ?gene ex:hasName ?geneName .
    FILTER NOT EXISTS {
      ?protein a ex:Protein ;
               ex:encodedBy ?gene .
      ?drug ex:hasTarget ?protein .
    }
  }
}
```

**How it works:** The query matches Enzyme nodes encoded by genes, then uses FILTER NOT EXISTS to exclude genes that also encode any Protein acting as a drug target.

### CQ20. Average number of targets per drug

**Question:** What is the average number of target proteins per drug, calculated only among drugs that possess at least one target?

```sparql
PREFIX ex: <http://example.org/drugkg/>

SELECT (AVG(?targetCount) AS ?avgTargets)
WHERE {
  {
    SELECT ?drug (COUNT(DISTINCT ?protein) AS ?targetCount)
    WHERE {
      GRAPH <http://example.org/drugkg/graphs/data> {
        ?drug a ex:Drug ;
              ex:hasTarget ?protein .
      }
    }
    GROUP BY ?drug
    HAVING(COUNT(DISTINCT ?protein) >= 1)
  }
}
```

**How it works:** A subquery counts targets per drug using COUNT and HAVING to include only drugs with at least one target. The outer query computes AVG over these counts.

### CQ21. Drugs, direct enzymes, pathway enzymes, and non-direct enzymes

**Question:** Find drugs, their direct enzymes, and the pathways they participate in. Then, identify other enzymes present in that same pathway that do not act directly on the initial drug.

```sparql
PREFIX ex: <http://example.org/drugkg/>

SELECT DISTINCT ?drugName ?directEnzymeName ?pathwayName ?otherEnzymeName
WHERE {
  GRAPH <http://example.org/drugkg/graphs/data> {
    ?drug a ex:Drug ;
          ex:hasName ?drugName ;
          ex:hasEnzyme ?directEnzyme ;
          ex:hasPathway ?pathway .
    OPTIONAL { ?directEnzyme ex:hasName ?directEnzymeName . }
    ?pathway ex:pathwayName ?pathwayName ;
             ex:pathwayHasEnzyme ?otherEnzyme .
    FILTER(?otherEnzyme != ?directEnzyme)
    OPTIONAL { ?otherEnzyme ex:hasName ?otherEnzymeName . }
  }
}
LIMIT 50
```

**How it works:** The query matches drug → hasEnzyme → directEnzyme and drug → hasPathway → pathway → pathwayHasEnzyme → otherEnzyme, then filters out the direct enzyme using FILTER != to find non-direct pathway enzymes.
