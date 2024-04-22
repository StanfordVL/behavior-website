---
title: BEHAVIOR-1K
subtitle: A Human-Centered, Embodied AI Benchmark with 1,000 Everyday Activities and Realistic Simulation
description: None
featured_image: /assets/img/behavior/b1k-feats/sim2real.png
# featured_video: /assets/img/behavior/hundred-tile-recording.m4v
show_release_alert: true
---

#### What is BEHAVIOR-1K?

BEHAVIOR-1K is a comprehensive simulation benchmark for human-centered robotics. Compared to its predecessor, BEHAVIOR-100, this new benchmark is more grounded on actual human needs: the 1,000 activities come from the results of an extensive survey on "what do you want robots to
do for you?". It is more diverse in the type of scenes, objects, and activities. Powered by [**NVIDIA's Omniverse**](https://www.nvidia.com/en-us/omniverse/), BEHAVIOR-1K also achieves a new level of realism in rendering and physics simulation. We hope that BEHAVIOR-1K’s human-grounded nature, diversity, and realism
make it valuable for embodied AI and robot learning research. 

<p class="alert alert-default">The first BEHAVIOR-1K full release (v1.0.0) is now available! This release features 1,004 pre-sampled activities, 50 scenes, ~10,000 objects, and many usability improvements. <a href="https://behavior.stanford.edu/omnigibson/getting_started/installation.html" class="alert-link">Get started!</a></p>

###### Reference
- [BEHAVIOR-1K: A Human-Centered, Embodied AI Benchmark with 1,000 Everyday Activities and Realistic Simulation](https://arxiv.org/abs/2403.09227). Chengshu Li\*, Ruohan Zhang\*, Josiah Wong\*, Cem Gokmen\*, Sanjana Srivastava\*, Roberto Martín-Martín\*, Chen Wang\*, Gabrael Levine\*, Wensi Ai\*, Benjamin Martinez, Hang Yin, Michael Lingelbach, Minjune Hwang, Ayano Hiranaka, Sujay Garlanka, Arman Aydin, Sharon Lee, Jiankai Sun, Mona Anvari, Manasi Sharma, Dhruva Bansal, Samuel Hunter, Kyu-Young Kim, Alan Lou, Caleb R Matthews, Ivan Villa-Renteria, Jerry Huayang Tang, Claire Tang, Fei Xia, Yunzhu Li, Silvio Savarese, Hyowon Gweon, C. Karen Liu, Jiajun Wu, Li Fei-Fei. Conference on Robot Learning (CoRL) 2022.

#### Building blocks of BEHAVIOR-1K
BEHAVIOR-1K includes two components. The first is the definition of 1,000 everyday activities, grounded in 50
scenes (houses, gardens, restaurants, offices, etc.) with more than 5,000 objects
annotated with rich physical and semantic properties. The second is OmniGibson (based on [**Nvidia's Omniverse**](https://www.nvidia.com/en-us/omniverse/)),
a novel simulation environment that supports these activities via realistic physics
simulation and rendering of rigid bodies, deformable bodies, and liquids. 

You can follow [installation guide](https://behavior.stanford.edu/omnigibson/getting_started/installation.html) to start using BEHAVIOR-1K for your research. The main components are:
###### * BEHAVIOR-1K benchmark [codebase](https://github.com/StanfordVL/OmniGibson) and [documentation](https://behavior.stanford.edu/omnigibson/).
###### * BEHAVIOR-1K scene and object assets (docs TBD).
###### * BEHAVIOR-1K [Activity definitions in Behavior Domain Definition Language (BDDL)](https://github.com/StanfordVL/bddl/tree/master/bddl/activity_definitions).

{% include components/features/b1k-demo-video.html %}


{% include components/features/b1k-feat.html %}



