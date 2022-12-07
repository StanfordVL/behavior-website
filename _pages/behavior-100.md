---
title: BEHAVIOR
subtitle: Benchmark for Everyday Household Activities in Virtual, Interactive, and Ecological Environments
description: None
featured_image: /assets/img/behavior/hundred-tile-recording.jpg
featured_video: /assets/img/behavior/hundred-tile-recording.m4v
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

#### Resources
[BEHAVIOR-100 benchmark code](https://github.com/StanfordVL/behavior) and [documentation](https://stanfordvl.github.io/behavior/intro.html).

[iGibson simulator code](https://github.com/StanfordVL/iGibson) and [documentation](http://svl.stanford.edu/igibson/docs/).

[BDDL specification language code and documentation](https://github.com/StanfordVL/bddl).


{% include components/features/join-us.html %}

{% include components/features/feature-1-B.html %}

#### References

- [BEHAVIOR: Benchmark for Everyday Household Activities in Virtual, Interactive, and Ecological Environments](https://arxiv.org/abs/2108.03332). Sanjana Srivastava\*, Chengshu Li\*, Michael Lingelbach\*, Roberto Martín-Martín\*, Fei Xia, Kent Vainio, Zheng Lian, Cem Gokmen, Shyamal Buch, C. Karen Liu, Silvio Savarese, Hyowon Gweon, Jiajun Wu, Li Fei-Fei, Conference on Robot Learning (CoRL) 2021.

- [iGibson 2.0: Object-Centric Simulation for Robot Learning of Everyday Household Tasks](https://arxiv.org/abs/2108.03272). Chengshu Li\*, Fei Xia\*, Roberto Martín-Martín\*, Michael Lingelbach, Sanjana Srivastava, Bokui Shen, Kent Vainio, Cem Gokmen, Gokul Dharan, Tanish Jain, Andrey Kurenkov, C. Karen Liu, Hyowon Gweon, Jiajun Wu, Li Fei-Fei, Silvio Savarese, Conference on Robot Learning (CoRL) 2021.

- [iGibson 1.0: A Simulation Environment for Interactive Tasks in Large Realistic Scenes](https://arxiv.org/abs/2012.02924). Bokui Shen\*, Fei Xia\*, Chengshu Li*, Roberto Martín-Martín\*, Linxi Fan, Guanzhi Wang, Shyamal Buch, Claudia D'Arpino, Sanjana Srivastava, Lyne P Tchapmi, Micael E Tchapmi, Kent Vainio, Li Fei-Fei, Silvio Savarese, Conference on Intelligent Robots and Systems (IROS) 2021.
