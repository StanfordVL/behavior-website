---
title: Creating BEHAVIOR Activity Definitions in BDDL
subtitle: Step-by-step guide to using our annotator to create new definitions for benchmarking embodied agents. 
# featured_image: /assets/img/behavior/iccv21.png
---

<!-- 1. **Define the activity.** Decide on an activity - either choose from the [BEHAVIOR activity list](https://behavior.stanford.edu/behavior-gallery/activity.html) or make up your own. Define the activity with our visual-BDDL annotator at the link below, with your own version of our annotation system (download the [code](https://github.com/StanfordVL/behavior-activity-annotator)), or write the BDDL directly - see the [original definitions](https://github.com/StanfordVL/bddl/tree/master/bddl/activity_definitions) for examples. Check if the definition fits in one or more simulator scenes by attempting sampling. 
2. **Sample the initial state into a scene.** Turn the symbolic BDDL initial state into a concrete physical state by sampling objects in the simulator scene such that they satisfy your initial condition. This can be done programmatically, scene-agnostically, and with potentially infinite variation by giving your BDDL definition as input to the [iGibson](https://github.com/StanfordVL/iGibson) sampling functionality. 
3. **Run your activity.** Initialize the agent and run the simulator, using BDDL goal checking functionality to track progress at every simulator step. 

Click [here](https://stanfordvl.github.io/behavior-activity-annotation/) to access the activity annotator. -->


Read through the instructions below for an overview on how to create an activity definition:
1. **Choose an activity you want to define**, like "putting away groceries" or "washing dishes". You can choose from the [list of BEHAVIOR activities](https://behavior.stanford.edu/behavior-gallery/activity.html) or you can make your own!
2. **Define the activity in BDDL.** You can do this a) with our visual-BDDL annotator at the link below, b) with your own version of our annotation system (download the [code](https://github.com/StanfordVL/behavior-activity-annotator)), or c) by writing your own BDDL file directly - see the [original definitions](https://github.com/StanfordVL/bddl/tree/master/bddl/activity_definitions) for examples. Note that our annotator has detailed instructions and checks your definition for correctness! Process for our online annotator:
    1. Enter your activity and choose rooms for it.
    2. Choose objects to use and add in your scene.
    3. If you want, read through an instruction sheet on visual BDDL - even if you know predicate logic well, you'll learn about our custom operators!
    4. Write an initial state and goal expression in BDDL. The initial state should be completely ground and concrete, not general - you're making an example for a robot to enter. The goal expression should define what success looks like given your initial state, and should be as general as possible. 
    5. If there are any issues with the BDDL, correct them based on the automated feedback.
    6. Collect your definition!

 You can now try out the activity annotator by clicking the link at the end of these instructions - it will have more guidance on how to create a definition. If you want to learn about next steps after creating a definition, keep reading! 

3. **Check the feasibility of your definition.** Your definition will be correct coming out of our annotator, but it might not fit in the scene - if you ask for thirty watermelons in one cabinet, it's probably not going to work out. To check the *feasibility* of your definition, try sampling it in iGibson 2.0 and edit it according to the sampler's feedback if necessary. Use [this example](https://github.com/StanfordVL/iGibson) of iGibson's sampling functionality as a guide to try your definition. If you'd like to use a different simulator, you can use the code called in the example to guide your implementation. 
4. **Use your awesome new activity definition to test embodied agents!** Also, let us know about it! The submission you make to our online annotator will not yet have been checked for feasibility, so once you have feasible definitions, you can submit to BEHAVIOR by making a pull request to the [`bddl` repo](https://github.com/StanfordVL/bddl/tree/master/bddl/activity_definitions).  
    

Click [here](https://stanfordvl.github.io/behavior-activity-annotation/) to access the activity annotator.

<!-- ## How to add a custom object 
For new activities and new definitions of existing activities, you may want to add new objects that don't yet exist in the BEHAVIOR Object Database. This can be done in TODO steps: 
### In the `bddl` repo 
1. Match your object to the [WordNet synset]() that best defines it. 
2. Select which properties apply to it from the following list: 
```
breakable
burnable
coldSource
cookable
dustyable
freezable
heatSource      # generates heat (e.g. microwave, stove)
liquid
openable
perishable
screwable
stainable
sliceable
slicer          # can slice a sliceable item (e.g. knife)
soakable        # can *become* wet 
timeSetable     
toggleable      # can be toggled on/off 
```
3. Add the following entry to [`bddl/utils/synsets_to_filtered_properties.json`](https://github.com/StanfordVL/bddl/blob/master/utils/synsets_to_filtered_properties.json):
```
"your_synset": {
    "your_property1": {},
    "your_property2": {},
    ...
    "your_property3": {}
}
```
If `cookable` or `burnable` are properties of your object, the property dict should include the cook/burn temperature. Example:
```
"your_synset": {
    "cookable": {"cook_temperature": your_cook_temp_float},
    "burnable": {"burn_temperature": your_burn_temp_float}
}
```
**The following steps assume that you are using iGibson 2.0:**
4. Edit [`bddl/utils/prune_object_property.py`](https://github.com/StanfordVL/bddl/blob/master/utils/prune_object_property.py) so that your synset is included in the pruned lists for each property. 
5. Run `python prune_object_property.py`. Check that your synset and its properties are in [`bddl/utils/synsets_to_filtered_properties_pruned_igibson.json`](https://github.com/StanfordVL/bddl/blob/master/utils/synsets_to_filtered_properties_pruned_igibson.json). If not, check your work on steps 3 and 4. 

### In the `iGibson` repo 
1.  -->
