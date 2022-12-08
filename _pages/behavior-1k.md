---
title: BEHAVIOR-1K
subtitle: A Benchmark for Embodied AI with 1,000 Everyday Activities and Realistic Simulation
description: None
featured_image: /assets/img/behavior/sim2real.png
# featured_video: /assets/img/behavior/hundred-tile-recording.m4v
---


#### What is BEHAVIOR-1K?

BEHAVIOR-1K is a comprehensive simulation benchmark for human-centered robotics. Compared to its predecessor, BEHAVIOR-100, BEHAVIOR-1K is more grounded on actual human needs. It is more diverse in the type of scenes, objects, and activities. Powered by Nvidia's Omniverse, BEHAVIOR-1K also achieves a new level of realism in rendering and physics simulation.  

BEHAVIOR-1K includes two components, guided and motivated by the results of an extensive survey on "what do you want robots to
do for you?" The first is the definition of 1,000 everyday activities, grounded in 50
scenes (houses, gardens, restaurants, offices, etc.) with more than 5,000 objects
annotated with rich physical and semantic properties. The second is OmniGibson,
a novel simulation environment that supports these activities via realistic physics
simulation and rendering of rigid bodies, deformable bodies, and liquids. We hope that BEHAVIOR-1K’s human-grounded nature, diversity, and realism
make it valuable for embodied AI and robot learning research. 


{% include components/features/b1k-features.html %}

#### Components



Do you want to benchmark your solution? Follow the instructions [here](https://stanfordvl.github.io/behavior/installation.html). You will download and install the required infrastructure: [a new version of iGibson](http://svl.stanford.edu/igibson/docs/installation.html), our simulation environment for interactive tasks extended now to new object states for BEHAVIOR, the BEHAVIOR Dataset of Objects and the iGibson2.0 Dataset of Scenes (combined in our [benchmarking bundle](https://storage.googleapis.com/gibson_scenes/behavior_data_bundle.zip)), with object and house models to use the benchmark, and our [starter code](https://github.com/StanfordVL/behavior/), with examplest to train againts in the tasks. 
<!-- If you want to use human demonstrations to start developing your solutions, you can also download the [BEHAVIOR Dataset of Human Demonstrations](https://behavior.stanford.edu/human_demonstrations/human_demonstrations.html) in virtual reality.
 -->

