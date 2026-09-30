"""Student submission file.

Each strategy must return a NEW RDFLib Graph fragment.
The pipeline will merge the fragment into the accumulated graph.

Important:
- Do not modify framework files.
- Use only the service wrappers and API methods documented in the readme.md.
- If a strategy depends on information produced by a previous strategy, it is your
  responsibility to enable the earlier strategy in config.json.
"""
from __future__ import annotations

from rdflib import Graph, Literal, RDF, RDFS, URIRef, XSD

from etl_core.registry import register_strategy


def _bind_namespaces(graph: Graph, ns_map) -> None:
    """Bind the configured prefixes to a graph fragment."""
    for prefix, namespace in ns_map.items():
        graph.bind(prefix, namespace)


def _slugify(text: str) -> str:
    """Create a simple local identifier from a label."""
    return "_".join(text.strip().lower().replace("/", " ").replace("-", " ").split())


@register_strategy("drug_core")
def drug_core(graph_so_far: Graph, etl_service) -> Graph:
    """Starter example.

    Current starter behaviour:
    - reads the seed DrugBank IDs from the provided CSV
    - creates one ex:Drug node per seed ID
    - adds ex:hasID with the DrugBank ID as a literal
    """
    ns = etl_service.get_namespaces()
    ex = ns["ex"]
    drug_ns = ns["drug"]

    g = Graph()
    _bind_namespaces(g, ns)

    for drug_id in etl_service.get_drug_ids():
        drug_uri = drug_ns[drug_id]
        g.add((drug_uri, RDF.type, ex.Drug))
        g.add((drug_uri, ex.hasID, Literal(drug_id)))
        g.add((drug_uri, RDFS.label, Literal(drug_id)))

        info = etl_service.get_drug_info(drug_id)

        if info.get("name"):
            g.add((drug_uri, ex.hasName, Literal(info["name"][0])))
            g.add((drug_uri, RDFS.label, Literal(info["name"][0])))

        if info.get("description"):
            g.add((drug_uri, ex.hasDescription, Literal(info["description"][0])))

        if info.get("indication"):
            g.add((drug_uri, ex.hasIndication, Literal(info["indication"][0])))

        if info.get("mechanism_of_action"):
            g.add((drug_uri, ex.hasMechanismOfAction, Literal(info["mechanism_of_action"][0])))

        if info.get("state"):
            g.add((drug_uri, ex.hasState, Literal(info["state"][0])))

        for group in info.get("group", []):
            g.add((drug_uri, ex.hasGroup, Literal(group)))

        for synonym in info.get("synonym", []):
            g.add((drug_uri, ex.hasSynonym, Literal(synonym)))

        family = etl_service.get_drug_family(drug_id)
        for mw in family.get("molecular-weight", []):
            try:
                g.add((drug_uri, ex.hasMolecularWeight, Literal(float(mw), datatype=XSD.float)))
            except ValueError:
                pass

    for drug_id_1, drug_id_2 in etl_service.get_drug_ddis():
        uri1 = drug_ns[drug_id_1]
        uri2 = drug_ns[drug_id_2]
        g.add((uri1, ex.interactsWith, uri2))
        g.add((uri2, ex.interactsWith, uri1))

    return g


@register_strategy("drug_mechanisms")
def drug_mechanisms(graph_so_far: Graph, etl_service) -> Graph:
    """Implement scope 2.

    Information scope:
    - targets
    - proteins
    - genes

    """
    ns = etl_service.get_namespaces()
    ex = ns["ex"]
    drug_ns = ns["drug"]
    protein_ns = ns["protein"]
    gene_ns = ns["gene"]

    g = Graph()
    _bind_namespaces(g, ns)

    all_uniprot_ids = []

    for drug_id in etl_service.get_drug_ids():
        drug_uri = drug_ns[drug_id]
        targets = etl_service.get_drug_targets(drug_id)

        for target in targets:
            for uniprot_id in target.get("uniprot_ids", []):
                all_uniprot_ids.append(uniprot_id)
                protein_uri = protein_ns[uniprot_id]

                g.add((protein_uri, RDF.type, ex.Protein))
                g.add((drug_uri, ex.hasTarget, protein_uri))

                if target.get("protein_names"):
                    g.add((protein_uri, ex.hasName, Literal(target["protein_names"][0])))
                    g.add((protein_uri, RDFS.label, Literal(target["protein_names"][0])))
                g.add((protein_uri, ex.hasUniProtID, Literal(uniprot_id)))

                for action in target.get("actions", []):
                    g.add((protein_uri, ex.hasAction, Literal(action)))

    if all_uniprot_ids:
        gene_id_map = etl_service.get_gene_ids(all_uniprot_ids)
        valid_gene_ids = [gid for gid in gene_id_map.values() if gid]

        if valid_gene_ids:
            gene_data_map = etl_service.get_gene_data(valid_gene_ids)

            for uniprot_id, gene_id in gene_id_map.items():
                if not gene_id:
                    continue
                protein_uri = protein_ns[uniprot_id]
                gene_uri = gene_ns[str(gene_id)]

                g.add((gene_uri, RDF.type, ex.Gene))
                g.add((protein_uri, ex.encodedBy, gene_uri))

                gene_info = gene_data_map.get(str(gene_id), {})
                if gene_info.get("name"):
                    g.add((gene_uri, ex.hasName, Literal(gene_info["name"])))
                    g.add((gene_uri, RDFS.label, Literal(gene_info["name"])))
                if gene_info.get("description"):
                    g.add((gene_uri, ex.hasGeneDescription, Literal(gene_info["description"])))

    return g


@register_strategy("drug_biological_context")
def drug_biological_context(graph_so_far: Graph, etl_service) -> Graph:
    """Implement scope 3.

    Information scope:
    - pathways
    - direct enzymes

    """
    ns = etl_service.get_namespaces()
    ex = ns["ex"]
    drug_ns = ns["drug"]
    protein_ns = ns["protein"]
    pathway_ns = ns["pathway"]

    g = Graph()
    _bind_namespaces(g, ns)

    for drug_id in etl_service.get_drug_ids():
        drug_uri = drug_ns[drug_id]

        pathways = etl_service.get_drug_pathways(drug_id)
        for pathway in pathways:
            for pathway_id in pathway.get("smpdb_id", []):
                pathway_uri = pathway_ns[pathway_id]
                g.add((pathway_uri, RDF.type, ex.Pathway))
                g.add((drug_uri, ex.hasPathway, pathway_uri))

                if pathway.get("name"):
                    g.add((pathway_uri, ex.pathwayName, Literal(pathway["name"][0])))
                    g.add((pathway_uri, RDFS.label, Literal(pathway["name"][0])))

                if pathway.get("category"):
                    g.add((pathway_uri, ex.pathwayCategory, Literal(pathway["category"][0])))

                g.add((pathway_uri, ex.pathwayHasDrug, drug_uri))

        enzymes = etl_service.get_drug_enzymes(drug_id)
        for enzyme in enzymes:
            for uniprot_id in enzyme.get("uniprot_ids", []):
                enzyme_uri = protein_ns[uniprot_id]
                g.add((enzyme_uri, RDF.type, ex.Enzyme))
                g.add((drug_uri, ex.hasEnzyme, enzyme_uri))

                if enzyme.get("protein_names"):
                    g.add((enzyme_uri, ex.hasName, Literal(enzyme["protein_names"][0])))
                    g.add((enzyme_uri, RDFS.label, Literal(enzyme["protein_names"][0])))

                g.add((enzyme_uri, ex.hasUniProtID, Literal(uniprot_id)))

                for action in enzyme.get("actions", []):
                    g.add((enzyme_uri, ex.hasAction, Literal(action)))

                for pathway in pathways:
                    for pathway_id in pathway.get("id", []):
                        pathway_uri = pathway_ns[pathway_id]
                        g.add((pathway_uri, ex.pathwayHasEnzyme, enzyme_uri))

    return g


@register_strategy("drug_network_context")
def drug_network_context(graph_so_far: Graph, etl_service) -> Graph:
    """Implement scope 4.

    Information scope:
    - protein interaction network
    - chemical classification hierarchy

    """
    ns = etl_service.get_namespaces()
    ex = ns["ex"]
    drug_ns = ns["drug"]
    protein_ns = ns["protein"]

    g = Graph()
    _bind_namespaces(g, ns)

    for drug_id in etl_service.get_drug_ids():
        drug_uri = drug_ns[drug_id]
        family = etl_service.get_drug_family(drug_id)

        if family.get("kingdom"):
            g.add((drug_uri, ex.hasKingdom, Literal(family["kingdom"][0])))

        if family.get("superclass"):
            g.add((drug_uri, ex.hasSuperclass, Literal(family["superclass"][0])))

        if family.get("class"):
            g.add((drug_uri, ex.hasClass, Literal(family["class"][0])))

        if family.get("subclass"):
            g.add((drug_uri, ex.hasSubclass, Literal(family["subclass"][0])))

        if family.get("direct_parent"):
            g.add((drug_uri, ex.hasDirectParent, Literal(family["direct_parent"][0])))

    all_uniprot_ids = []
    for drug_id in etl_service.get_drug_ids():
        targets = etl_service.get_drug_targets(drug_id)
        for target in targets:
            for uniprot_id in target.get("uniprot_ids", []):
                all_uniprot_ids.append(uniprot_id)
    if all_uniprot_ids:
        string_id_map = etl_service.get_string_ids(all_uniprot_ids)
        valid_string_ids = [sid for sid in string_id_map.values() if sid]

        if valid_string_ids:
            ppis = etl_service.get_ppis(valid_string_ids)
            uniprot_by_string = {v: k for k, v in string_id_map.items() if v}

            for string_id_1, string_id_2 in ppis:
                uniprot_1 = uniprot_by_string.get(string_id_1)
                uniprot_2 = uniprot_by_string.get(string_id_2)

                if uniprot_1 and uniprot_2:
                    protein_uri_1 = protein_ns[uniprot_1]
                    protein_uri_2 = protein_ns[uniprot_2]
                    g.add((protein_uri_1, ex.interactsWithProtein, protein_uri_2))
                    g.add((protein_uri_2, ex.interactsWithProtein, protein_uri_1))

    return g
