---
title: BEHAVIOR-100
subtitle: Benchmark for 100 Everyday Household Activities in Virtual, Interactive, and Ecological Environments
description: None
featured_image: /assets/img/behavior/hundred-tile-recording.jpg
featured_video: /assets/img/behavior/hundred-tile-recording.m4v
---


#### What is BEHAVIOR-100?

BEHAVIOR-100 is the first generation of BEHAVIOR, a benchmark for embodied AI with 100 activities in simulation, spanning a range of everyday household chores such as cleaning, maintenance, and food preparation. These activities are designed to be realistic, diverse and complex, aiming to reproduce the challenges that agents must face in the real world. 

###### Reference
- [BEHAVIOR: Benchmark for Everyday Household Activities in Virtual, Interactive, and Ecological Environments](https://arxiv.org/abs/2108.03332). Sanjana Srivastava\*, Chengshu Li\*, Michael Lingelbach\*, Roberto Martín-Martín\*, Fei Xia, Kent Vainio, Zheng Lian, Cem Gokmen, Shyamal Buch, C. Karen Liu, Silvio Savarese, Hyowon Gweon, Jiajun Wu, Li Fei-Fei, Conference on Robot Learning (CoRL) 2021.

#### Building blocks of BEHAVIOR-100
Building BEHAVIOR-100 poses three fundamental difficulties for each activity: definition, instantiation in a simulator, and evaluation. BEHAVIOR addresses these with three building blocks. First, we propose a predicate logic-based description language (BDDL) for expressing an activity’s initial and goal conditions, enabling generation of diverse instances for any activity. Second, we identify the simulator-agnostic features required by an underlying environment to support BEHAVIOR-100, and demonstrate in one such simulator, i.e., iGibson 2.0. Third, we introduce a set of metrics to measure task progress and efficiency, absolute and relative to human demonstrators. We include 500 human demonstrations in virtual reality (VR) to serve as the human ground truth. 

Do you want to benchmark your solution? Follow the instructions [here](https://stanfordvl.github.io/behavior/installation.html) to get started. The main components are:

###### * BEHAVIOR-100 benchmark [codebase](https://github.com/StanfordVL/behavior) and [documentation](https://stanfordvl.github.io/behavior/intro.html).
###### * iGibson simulator [codebase](https://github.com/StanfordVL/iGibson) and [documentation](http://svl.stanford.edu/igibson/docs/).
###### * Combined BEHAVIOR-100 iGibson2.0 [scene and object assets](https://storage.googleapis.com/gibson_scenes/behavior_data_bundle.zip).
###### * BDDL specification language [codebase and documentation](https://github.com/StanfordVL/bddl).
###### * BEHAVIOR-100 VR human demonstration [dataset](https://behavior.stanford.edu/vr-demos).

<!-- You will download and install the required infrastructure: [a new version of iGibson](http://svl.stanford.edu/igibson/docs/installation.html), our simulation environment for interactive tasks extended now to new object states for BEHAVIOR, the BEHAVIOR Dataset of Objects and the iGibson2.0 Dataset of Scenes (combined in our [benchmarking bundle](https://storage.googleapis.com/gibson_scenes/behavior_data_bundle.zip)), with object and house models to use the benchmark, and our [starter code](https://github.com/StanfordVL/behavior/), with examplest to train againts in the tasks.  -->

{% include components/features/b100-feat.html %}

<!-- {% include components/features/feature-3-C.html %} -->




