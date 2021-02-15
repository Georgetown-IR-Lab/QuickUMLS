HEADERS_MRCONSO = [
    "cui",
    "lat",
    "ts",
    "lui",
    "stt",
    "sui",
    "ispref",
    "aui",
    "saui",
    "scui",
    "sdui",
    "sab",
    "tty",
    "code",
    "str",
    "srl",
    "suppress",
    "cvf",
]
HEADERS_MRSTY = ["cui", "sty", "hier", "desc", "sid", "num"]

NEGATIONS = {"none", "non", "neither", "nor", "no", "not"}

# The following is a list of all existing semtypes along with their name and some examples.
# You can easily select the ones you need by commenting out the lines that are not relevant for your application.

ACCEPTED_SEMTYPES = {
    # 'T020', # Acquired Abnormality, ex.: Hemorrhoids; Hernia, Femoral; Cauliflower ear
    # 'T052', # Activity, ex.: Expeditions; Information Distribution; Social Planning
    # 'T100', # Age Group, ex.: Adult; Infant, Premature; Adolescent (age group)
    # 'T087', # Amino Acid Sequence, ex.: Signal Peptides; Homologous Sequences, Amino Acid; Abnormal amino acid
    # 'T116', # Amino Acid, Peptide, or Protein, ex.: Amino Acids, Cyclic; Glycopeptides; Keratin
    # 'T011', # Amphibian, ex.: Salamandra; Urodela; Brazilian horned frog
    # 'T190', # Anatomical Abnormality, ex.: Bronchial Fistula; Foot Deformities; Hyperostosis of skull
    # 'T017', # Anatomical Structure, ex.: Cadaver; Pharyngostome; Anatomic structures
    # 'T008', # Animal, ex.: Animals; Animals, Laboratory; Carnivore
    "T195",  # Antibiotic, ex.: Antibiotics; bactericide; Thienamycins
    # 'T194', # Archaeon, ex.: Thermoproteales; Haloferax volcanii; Methanospirillum
    # 'T007', # Bacterium, ex.: Acetobacter; Bacillus cereus; Cytophaga
    # 'T053', # Behavior, ex.: Homing Behavior; Sexuality; Habitat Selection
    # 'T038', # Biologic Function, ex.: Antibody Formation; Drug resistance; Homeostasis
    # 'T123', # Biologically Active Substance, ex.: Cytokinins; Pheromone
    # 'T091', # Biomedical Occupation or Discipline, ex.: Adolescent Medicine; Cellular Neurobiology; Dentistry
    # 'T122', # Biomedical or Dental Material, ex.: Acrylic Resins; Bone Cements; Dentifrices
    # 'T012', # Bird, ex.: Serinus; Ducks; Quail
    "T029",  # Body Location or Region, ex.: Forehead; Sublingual Region; Base of skull structure
    "T023",  # Body Part, Organ, or Organ Component, ex.: Aorta; Brain Stem; Structure of neck of femur
    # 'T030', # Body Space or Junction, ex.: Knee joint; Greater sac of peritoneum; Synapses
    "T031",  # Body Substance, ex.: Amniotic Fluid; saliva; Smegma
    # 'T022', # Body System, ex.: Endocrine system; Renin-angiotensin system; Reticuloendothelial System
    # 'T088', # Carbohydrate Sequence, ex.: Carbohydrate Sequence; Abnormal carbohydrate sequence
    # 'T025', # Cell, ex.: B-Lymphocytes; Dendritic Cells; Fibroblasts
    # 'T026', # Cell Component, ex.: Axon; Golgi Apparatus; Organelles
    # 'T043', # Cell Function, ex.: Cell Cycle; Cell division; Phagocytosis
    # 'T049', # Cell or Molecular Dysfunction, ex.: DNA Damage; Wallerian Degeneration; Atypical squamous metaplasia
    # 'T103', # Chemical, ex.: Acids; Chemicals; Ionic Liquids
    # 'T120', # Chemical Viewed Functionally, ex.: Aerosol Propellants; Detergents; Stabilizing Agents
    # 'T104', # Chemical Viewed Structurally, ex.: Ammonium Compounds; Cations; Sulfur Compounds
    # 'T185', # Classification, ex.: Anatomy (MeSH Category); Tumor Stage Classification; axis i
    "T201",  # Clinical Attribute, ex.: Bone Density; heart rate; Range of Motion, Articular
    "T200",  # Clinical Drug, ex.: Ranitidine 300 MG Oral Tablet [Zantac]; Aspirin 300 MG Delayed Release Oral
    # 'T077', # Conceptual Entity, ex.: Geographic Factors; Fractals; Secularism
    # 'T019', # Congenital Abnormality, ex.: Albinism; Cleft palate with cleft lip; Polydactyly of toes
    # 'T056', # Daily or Recreational Activity, ex.: Badminton; Dancing; Swimming
    "T060",  # Diagnostic Procedure, ex.: Biopsy; Heart Auscultation; Magnetic Resonance Imaging
    "T047",  # Disease or Syndrome, ex.: Diabetes Mellitus; Drug Allergy; Malabsorption Syndrome
    "T203",  # Drug Delivery Device, ex.: Nordette 21 Day Pack; {7 (Terazosin 1 MG Oral Tablet) / 7 (Terazosin 2 MG
    # 'T065', # Educational Activity, ex.: Academic Training; Family Planning Training; Preceptorship
    # 'T196', # Element, Ion, or Isotope, ex.: Carbon; Chromium Isotopes; Radioisotopes
    # 'T018', # Embryonic Structure, ex.: Blastoderm; Fetus; Neural Crest
    # 'T071', # Entity, ex.: Gifts, Financial; Image; Product Part
    # 'T069', # Environmental Effect of Humans, ex.: Air Pollution; Desertification; Bioremediation
    # 'T126', # Enzyme, ex.: GTP Cyclohydrolase II; enzyme substrate complex; arginine amidase
    # 'T204', # Eukaryote, ex.: Order Acarina; Bees; Plasmodium malariae
    # 'T051', # Event, ex.: Anniversaries; Exposure to Mumps virus (event); Device Unattended
    # 'T050', # Experimental Model of Disease, ex.: Alloxan Diabetes; Liver Cirrhosis, Experimental; Transient Gene Knock-Out
    # 'T099', # Family Group, ex.: Daughter; Is an only child; Unmarried Fathers
    "T033",  # Finding, ex.: Birth History; Downward displacement of diaphragm; Decreased glucose level
    # 'T013', # Fish, ex.: Bass; Salmonidae; Whitefish
    # 'T168', # Food, ex.: Beverages; Egg Yolk (Dietary); Ice Cream
    # 'T021', # Fully Formed Anatomical Structure, ex.: Entire body as a whole; Female human body; Set of parts of human body
    # 'T169', # Functional Concept, ex.: Interviewer Effect; Problem Formulation; Endogenous
    # 'T004', # Fungus, ex.: Aspergillus clavatus; Blastomyces; Neurospora
    # 'T028', # Gene or Genome, ex.: Alleles; Genome, Human; rRNA Operon
    # 'T045', # Genetic Function, ex.: Early Gene Transcription; Gene Amplification; RNA Splicing
    # 'T083', # Geographic Area, ex.: Baltimore; Canada; Far East
    # 'T064', # Governmental or Regulatory Activity, ex.: Certification; Credentialing; Public Policy
    # 'T096', # Group, ex.: Focus Groups; jury; teams
    # 'T102', # Group Attribute, ex.: Family Size; Group Structure; Life Expectancy
    # 'T131', # Hazardous or Poisonous Substance, ex.: Carcinogens; Fumigant; Mutagens
    "T058",  # Health Care Activity, ex.: ambulatory care services; Clinic Activities; Preventive Health Services
    # 'T093', # Health Care Related Organization, ex.: Centers for Disease Control and Prevention (U.S.); Halfway Houses;
    # 'T125', # Hormone, ex.: Enteric Hormones; thymic humoral factor; Prohormone
    # 'T016', # Human, ex.: Homo sapiens; jean piaget; Member of public
    # 'T068', # Human-caused Phenomenon or Process, ex.: Baby Boom; Cultural Evolution; Mass Media
    # 'T078', # Idea or Concept, ex.: Capitalism; Civil Rights; Ethics
    # 'T129', # Immunologic Factor, ex.: Antigens; Immunologic Factors; Blood group antigen P
    "T130",  # Indicator, Reagent, or Diagnostic Aid, ex.: Fluorescent Dyes; Indicators and Reagents; India ink stain
    # 'T055', # Individual Behavior, ex.: Assertiveness; Grooming; Risk-Taking
    "T037",  # Injury or Poisoning, ex.: Accidental Falls; Carbon Monoxide Poisoning; Snake Bites
    # 'T197', # Inorganic Chemical, ex.: Carbonic Acid; aluminum nitride; ferric citrate
    "T170",  # Intellectual Product, ex.: Decision Support Techniques; Information Systems; Literature
    "T034",  # Laboratory or Test Result, ex.: Blood Flow Velocity; Serum Calcium Level; Spinal Fluid Pressure
    "T059",  # Laboratory Procedure, ex.: Blood Protein Electrophoresis; Crystallography; Radioimmunoassay
    # 'T171', # Language, ex.: Armenian language; braille; Bilingualism
    # 'T066', # Machine Activity, ex.: Computer Simulation; Equipment Failure; Natural Language Processing
    # 'T015', # Mammal, ex.: Ursidae Family; Hamsters; Macaca
    # 'T073', # Manufactured Object, ex.: car seat; Cooking and Eating Utensils; Goggles
    "T074",  # Medical Device, ex.: Bone Screws; Headgear, Orthodontic; Compression Stockings
    "T048",  # Mental or Behavioral Dysfunction, ex.: Agoraphobia; Cyclothymic Disorder; Frigidity
    "T041",  # Mental Process, ex.: Anger; Auditory Fatigue; Avoidance Learning
    # 'T063', # Molecular Biology Research Technique, ex.: Northern Blotting; Genetic Engineering; In Situ Hybridization
    # 'T044', # Molecular Function, ex.: Binding, Competitive; Electron Transport; Glycolysis
    # 'T085', # Molecular Sequence, ex.: Genetic Code; Homologous Sequences; Molecular Sequence
    # 'T070', # Natural Phenomenon or Process, ex.: Air Movements; Corrosion; Lightning (phenomenon)
    "T191",  # Neoplastic Process, ex.: Abdominal Neoplasms; Bowen's Disease; Polyp in nasopharynx
    # 'T114', # Nucleic Acid, Nucleoside, or Nucleotide, ex.: Cytosine Nucleotides; Guanine; Oligonucleotides
    # 'T086', # Nucleotide Sequence, ex.: Base Sequence; Direct Repeat; RNA Sequence
    # 'T090', # Occupation or Discipline, ex.: Aviation; Craniology; Ecology
    # 'T057', # Occupational Activity, ex.: Collective Bargaining; Commerce; Containment of Biohazards
    # 'T042', # Organ or Tissue Function, ex.: Osteogenesis; Renal Circulation; Tooth Calcification
    # 'T109', # Organic Chemical, ex.: Benzene Derivatives
    # 'T001', # Organism, ex.: Organism; Infectious agent; Heterotroph
    # 'T032', # Organism Attribute, ex.: Age; Birth Weight; Eye Color
    "T040",  # Organism Function, ex.: Breeding; Hibernation; Motor Skills
    # 'T092', # Organization, ex.: Labor Unions; United Nations; Boarding school
    "T046",  # Pathologic Function, ex.: Inflammation; Shock; Thrombosis
    # 'T101', # Patient or Disabled Group, ex.: Amputees; Institutionalized Child; Mentally Ill Persons
    "T121",  # Pharmacologic Substance, ex.: Antiemetics; Cardiovascular Agents; Alka-Seltzer
    "T067",  # Phenomenon or Process, ex.: Disasters; Motor Traffic Accidents; Depolymerization
    # 'T072', # Physical Object, ex.: Printed Media; Meteors; Physical object
    "T039",  # Physiologic Function, ex.: Biorhythms; Hearing; Vasodilation
    # 'T002', # Plant, ex.: Aloe; Pollen; Helianthus species
    # 'T098', # Population Group, ex.: Asian Americans; Ethnic group; Adult Offenders
    # 'T097', # Professional or Occupational Group, ex.: Clergy; Demographers; Hospital Volunteers
    # 'T094', # Professional Society, ex.: American Medical Association; International Council of Nurses; Library
    # 'T080', # Qualitative Concept, ex.: Clinical Competence; Consumer Satisfaction; Health Status
    # 'T081', # Quantitative Concept, ex.: Age Distribution; Metric System; Selection Bias
    # 'T192', # Receptor, ex.: Binding Sites; Lymphocyte antigen CD4 receptor; integrin alpha11beta1
    # 'T089', # Regulation or Law, ex.: Building Codes; Criminal Law; Health Planning Guidelines
    # 'T014', # Reptile, ex.: Alligators; Water Mocassin; Genus Python (organism)
    # 'T062', # Research Activity, ex.: Animal Experimentation; Biomedical Research; Experimental Replication
    # 'T075', # Research Device, ex.: Electrodes, Enzyme; DNA Microarray Chip; Particle Count and Size Analyzer
    # 'T095', # Self-help or Relief Organization, ex.: Alcoholics Anonymous; Charities - organization; Red Cross
    "T184",  # Sign or Symptom, ex.: Dyspnea; Nausea; Pain
    # 'T054', # Social Behavior, ex.: Acculturation; Communication; Interpersonal Relations
    # 'T082', # Spatial Concept, ex.: Mandibular Rest Position; Lateral; Extrinsic
    # 'T167', # Substance, ex.: Air (substance); Fossils; Plastics
    # 'T079', # Temporal Concept, ex.: Birth Intervals; Half-Life; Postoperative Period
    "T061",  # Therapeutic or Preventive Procedure, ex.: Cesarean section; Dermabrasion; Family psychotherapy
    # 'T024', # Tissue, ex.: Cartilage; Endothelium; Epidermis
    # 'T010', # Vertebrate, ex.: Vertebrates; Gnathostomata vertebrate; Craniata <chordata>
    # 'T005', # Virus, ex.: Coliphages; Echovirus; Parvoviridae
    # 'T127'  # Vitamin, ex.: 5,25-Dihydroxy cholecalciferol; alpha-tocopheryl oxalate; Vitamin A [EPC]
}

UNICODE_DASHES = {
    u"\u002d",
    u"\u007e",
    u"\u00ad",
    u"\u058a",
    u"\u05be",
    u"\u1400",
    u"\u1806",
    u"\u2010",
    u"\u2011",
    u"\u2010",
    u"\u2012",
    u"\u2013",
    u"\u2014",
    u"\u2015",
    u"\u2053",
    u"\u207b",
    u"\u2212",
    u"\u208b",
    u"\u2212",
    u"\u2212",
    u"\u2e17",
    u"\u2e3a",
    u"\u2e3b",
    u"\u301c",
    u"\u3030",
    u"\u30a0",
    u"\ufe31",
    u"\ufe32",
    u"\ufe58",
    u"\ufe63",
    u"\uff0d",
}

# language with missing value
# will not have support for tokenization
LANGUAGES = {
    "BAQ": None,  # Basque
    "CHI": None,  # Chinese
    "CZE": None,  # Czech
    "DAN": "danish",  # Danish
    "DUT": "dutch",  # Dutch
    "ENG": "english",  # English
    "EST": None,  # Estonian
    "FIN": "finnish",  # Finnish
    "FRE": "french",  # French
    "GER": "german",  # German
    "GRE": "greek",  # Greek
    "HEB": None,  # Hebrew
    "HUN": "hungarian",  # Hungarian
    "ITA": "italian",  # Italian
    "JPN": None,  # Japanese
    "KOR": None,  # Korean
    "LAV": None,  # Latvian
    "NOR": "norwegian",  # Norwegian
    "POL": "polish",  # Polish
    "POR": "portoguese",  # Portuguese
    "RUS": "russian",  # Russian
    "SCR": None,  # Croatian
    "SPA": "spanish",  # Spanish
    "SWE": "swedish",  # Swedish
    "TUR": "turkish",  # Turkish
}

DOMAIN_SPECIFIC_STOPWORDS = {"time"}

SPACY_LANGUAGE_MAP = {
    "ENG": "en_core_web_sm",
    "GER": "de_core_web_sm",
    "SPA": "es_core_web_sm",
    "POR": "pt_core_web_sm",
    "FRE": "fr_core_web_sm",
    "ITA": "it_core_web_sm",
    "DUT": "nl_core_web_sm",
    "XXX": "xx",
}
