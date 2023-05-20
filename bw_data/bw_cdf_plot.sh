#!/bin/bash
file1=cook_all_cdf.txt
file2=cooked_traces_cdf.txt
file3=cooked_test_traces_cdf.txt
file4=Oboe_traces_cdf.txt
file5=oboe_train_traces_cdf.txt
file6=oboe_test_traces_cdf.txt
name=bw-trace-cdf
output=${name}
format=png
gnuplot<<!
set grid
set key right bottom
set xlabel "average bandwidth/Mbps" 
set ylabel "CDF"
set xrange [0:6]
set yrange [0:1.0]
set term "${format}"
set output "${output}-cdf.${format}"
plot "${file1}" u 2:3 title "dataset1" with points lw 2,\
"${file2}" u 2:3 title "dataset1-train" with points lw 2,\
"${file3}" u 2:3 title "dataset1-test" with points lw 2,\
"${file4}" u 2:3 title "dataset2" with points lw 2,\
"${file5}" u 2:3 title "dataset2-train" with points lw 2,\
"${file6}" u 2:3 title "dataset2-test" with points lw 2
set output
exit
!
