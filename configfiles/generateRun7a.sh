#!/bin/bash

snap=141

for sampling in 0 3 4; do

    for noise in 0 1 2 3; do

	for r in 2 5 8 14; do

	    for mc in c4 duffy; do

		for coresize in 0 5 11 none; do

		    config=${mc}-r${r}-n${sampling}_${noise}_core${coresize}
		    dir=../mxxl_imperial/snap$snap/intlength400/$config
		    mkdir $dir
		    cat base.sh maxlike.sh bk11.sh ${mc}.sh r${r}.sh n${sampling}_${noise}.sh core_${coresize}.sh > $dir/config.sh
		    
		    echo $config >> ../run7a
		    
		done

	    done

	done

    done

done
