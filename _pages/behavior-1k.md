---
title: BEHAVIOR-1K
subtitle: A Benchmark for Embodied AI with 1,000 Everyday Activities and Realistic Simulation
description: None
featured_image: /assets/img/behavior/b1k-scenes.png
# featured_video: /assets/img/behavior/hundred-tile-recording.m4v
---


#### What is BEHAVIOR?

BEHAVIOR is a simulation benchmark to evaluate Embodied AI solutions.

Embodied artificial intelligence (EAI) is advancing. But where are we now? We propose to test EAI agents with the physical challenges humans solve in their everyday life: household activities such as picking up toys, setting the table, or cleaning floors. BEHAVIOR is a benchmark in simulation where EAI agents need to plan and execute navigation and manipulation strategies based on sensor information to fulfill 100 household activities.

BEHAVIOR tests the ability of agents to perceive the environment, plan, and execute complex long-horizon activities that involve multiple objects, rooms, and state changes, all with the reproducibility, safety and observability offered by a realistic physics simulation. To compare the performance of EAI agents to that of humans, we have collected human demonstrations in the same tasks and environments using virtual reality. The demonstrations serve as reference to compare EAI solutions, but they also be used to develop them.
<!-- 
[Technical details about the benchmark](/_pages/benchmark_guide.md) -->

{% include components/features/feature-3-B.html %}

#### Getting started

Do you want to benchmark your solution? Follow the instructions [here](https://stanfordvl.github.io/behavior/installation.html). You will download and install the required infrastructure: [a new version of iGibson](http://svl.stanford.edu/igibson/docs/installation.html), our simulation environment for interactive tasks extended now to new object states for BEHAVIOR, the BEHAVIOR Dataset of Objects and the iGibson2.0 Dataset of Scenes (combined in our [benchmarking bundle](https://storage.googleapis.com/gibson_scenes/behavior_data_bundle.zip)), with object and house models to use the benchmark, and our [starter code](https://github.com/StanfordVL/behavior/), with examplest to train againts in the tasks. 
<!-- If you want to use human demonstrations to start developing your solutions, you can also download the [BEHAVIOR Dataset of Human Demonstrations](https://behavior.stanford.edu/human_demonstrations/human_demonstrations.html) in virtual reality.
 -->

