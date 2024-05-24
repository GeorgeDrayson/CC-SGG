# CC-SGG: Corner Case Scenario Generation using Learned Scene Graphs
<br/>

In this work, we introduce a novel approach based on Heterogeneous Graph Neural Networks (HGNNs) to transform regular driving scenarios into corner cases. To achieve this, we first generate concise representations of regular driving scenes as scene graphs, minimally manipulating their structure and properties. Our model then learns to perturb those graphs to generate corner cases using attention and triple embeddings. The input and perturbed graphs are then imported back into the simulation to generate corner case scenarios. Our model successfully learned to produce corner cases from input scene graphs, achieving 89.9% prediction accuracy on our testing dataset. We further validate the generated scenarios on baseline autonomous driving methods, demonstrating our model's ability to effectively create critical situations for the baselines.

Find the paper [here](https://arxiv.org/abs/2309.09844)

<br/>

## File structure
<br/>

    ├── dataset/                       # Contains the dataset of driving scenarios
    │   ├── images/                        # Folder of images of each scene graph images
    │   ├── tensors/                       # Folder of tensors representing each scene graph
    │   ├── *.png                          # Ground truth (corner case) scene graph images
    │   ├── *.pt                           # Ground truth (corner case) scene graph tensor
    │   ├── semantics.json                 # Json containing extracted scenario semantics
    ├── model/                         # All files related to the GNN model
    ├── openscenario_generator/        # Methods to generate openscenario file from model prediction
    │   ├── generate_corner_case.py        # Main function for generating corner cases
    │   ├── extract_sceario_information.py # Create scene graph from model prediction
    │   ├── scenario.py                    # Class for creating an OPENSCENARIO file from a scene graph
    ├── scenarios/                     # Folder of OPENSCENARIO files used to generate the dataset
    ├── scene_graph_extractor/         # Methods to generate scene graphs from scenario semantics
    │   ├── main.py                        # Main function
    │   ├── scene_graph_files/             # Folder of extracted scene graph images and tensors
    │   ├── dataset.py                     # Class for saving the scene graphs
    │   ├── edge_extractor.py              # Class for extracting relations (edges) between scene graph nodes
    │   ├── scene_graph.py                 # Class for representing scene graphs
    │   ├── scene_graph_extractor.py       # Class for loading the semantic JSON files and extracting scene graphs 
    │   ├── sg_config.yaml                 # Config file for configuring scene graph representations
    ├── semantics_extractor/           # Methods to extract semantics from CARLA scenarios
    │   ├── main.py                        # Main function
    │   ├── semantic_files/                # Folder of JSON files containing extracted semantics
    │   ├── actor.py                       # Actor class for extracting static and dynamic attributes
    │   ├── carla_world.py                 # CARLA world class for connecting to the CARLA world
    │   ├── lane_extractor.py              # Class for lane extraction
    │   ├── semantics_extractor.py         # Class for semantics extraction
    ├── requirements.txt               # Dependencies
    └── README.md                      # README.md

## 1. Run OPENSCENARIO files (from the scenarios dataset) in CARLA:

### Prerequisites:

* [CARLA](https://carla.org/) 
* Matching [Scenario Runner release](https://github.com/carla-simulator/scenario_runner/releases)  

### Terminal 1:
**Start CARLA**
```
cd /opt/carla-simulator
./CarlaUE4.sh
```
Alternatively, to run in low-res mode:
```
./CarlaUE4.sh -quality-level=Low
```

### Terminal 2:
**Run scenario runner using an OPENSCENARIO (.xosc) file**
```
cd <scenario_runner folder>
python3 scenario_runner.py --openscenario <scenario filepath>
```  

For example:
```
python scenario_runner.py --openscenario ..\4yp-cornercases\testScenarios\FirstScenario.xosc
```

### Terminal 3:
**Start manual control**
```
cd <scenario_runner folder>
python3 manual_control.py
```
<br/>

## 2. Extract semantics from a scenario
**In a separate terminal run this script to extract semantics from CARLA and store them in a JSON file**

```
cd semantics_extractor
python main.py
```

## 3. Extract scene graphs from scenario semantics

**After extracting the semantics, generate scene graphs for each frame**
```
cd scene_graph_extractor
python main.py
```

## 4. Train a model on a scene graph dataset

**Train a model using these scene graphs**
```
cd model
python main.py
```

## 5. Use trained model to generate a corner case (includes predicting scene graph, extracting scenario information and generating an OPENSCENARIO file)

**Inference this model to generate new corner case graphs**
```
cd openscenario_generator
python generate_corner_case.py
```
