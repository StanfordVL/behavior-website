---
title: BEHAVIOR-1K
subtitle: A Benchmark for Embodied AI with 1,000 Everyday Activities and Realistic Simulation
description: None
featured_image: /assets/img/behavior/sim2real.png
# featured_video: /assets/img/behavior/hundred-tile-recording.m4v
---


#### What is BEHAVIOR-1K?

BEHAVIOR-1K is a comprehensive simulation benchmark for human-centered robotics. Compared to its predecessor, BEHAVIOR-100, this new benchmark is more grounded on actual human needs: the 1,000 activities come from the results of an extensive survey on "what do you want robots to
do for you?". It is more diverse in the type of scenes, objects, and activities. Powered by Nvidia's Omniverse, BEHAVIOR-1K also achieves a new level of realism in rendering and physics simulation. We hope that BEHAVIOR-1K’s human-grounded nature, diversity, and realism
make it valuable for embodied AI and robot learning research. 

#### Building blocks of BEHAVIOR-1K
BEHAVIOR-1K includes two components. The first is the definition of 1,000 everyday activities, grounded in 50
scenes (houses, gardens, restaurants, offices, etc.) with more than 5,000 objects
annotated with rich physical and semantic properties. The second is OmniGibson (based on Nvidia's Omniverse),
a novel simulation environment that supports these activities via realistic physics
simulation and rendering of rigid bodies, deformable bodies, and liquids. 

* [BEHAVIOR-1K Activity definitions in Behavior Domain Definition Language (BDDL)](https://github.com/StanfordVL/bddl).

* [BEHAVIOR-1K benchmark codebase](https://github.com/StanfordVL/behavior) and [documentation](https://stanfordvl.github.io/behavior/intro.html).

You can follow [installation guide]() to start using BEHAVIOR-1K for your research.

{% include components/features/b1k-feat2.html %}



