'use strict';

app.controller('GraphCtrl',
    [
        '$scope',
        function (
            $scope
        )
    {


    /*
        using the d3 select we append an element as the last child
        to the current selection
     */

//          <svg width="50" height="50">
//              <circle cx="25" cy="25" r="25" fill="purple" />
//          </svg>
    d3.select('body')
        .append('svg')
        .attr('width', 50)
        .attr('height', 50)
        .append('circle')
        .attr('cx', 25)
        .attr('cy', 25)
        .attr('r', 25)
        .style('fill', 'purple');

var selectionBody = d3.select('body');

var svgSelection = selectionBody.append('svg')
                                .attr('width', 50)
                                .attr('height', 50);

var circleSelection = svgSelection.append('circle')
                                .attr('cx', 25)
                                .attr('cy', 25)
                                .attr('r', 25)
                                .style('fill', 'purple');


// var theData = [1,2,3]
// var p = d3.select("body")
//     .selectAll("p") //although the p is not present we can use virtual selections later on
//     .data(theData)  //binds the data to the preselected p. almost acting like a loop (allows sticky to the selected DOM element)
//     .enter() //use enter() as the virtual selection to create a reference to our selectAll
//     .append("p") //we must use either append, enter or select after the virtual selection to create the element
//     .text("hello") //add the text
// }]);


var theData = [1,2,3]
var p = d3.select("body")
    .selectAll("p") //although the p is not present we can use virtual selections later on
    .data(theData)  //binds the data to the preselected p. almost acting like a loop (allows sticky to the selected DOM element)
    .enter() //use enter() as the virtual selection to create a reference to our selectAll
    .append("p") //we must use either append, enter or select after the virtual selection to create the element
    .text( function (d) { return d; } ); // for each of the data binded retrun the data (basically execute the function for each element)
    // d is a variable provided by d3 which denotes the current value of the data
    // this refers to the current DOM element
    // i refers to the current index of the data


// create a circle
var circleRadii = [40, 20, 10];

// create just the svg elemtn
var d3Selection = d3.select('body');
var svgSelection = d3Selection.append('svg')
                            .attr('width', 600)
                            .attr('height', 100);

// create circles based on the radius
var circles = svgSelection.selectAll('circle')
                                .data(circleRadii)
                                .enter()
                                .append('circle')

// apply attributes to each circle
var circleAttr = circles.attr('cx', 50)
                        .attr('cy', 50)
                        .attr('r', function (d) {
                            return d
                        })
                        .style('fill', function (d) {
                            var returnColor;
                            if (d === 40) { returnColor = "green";
                            } else if (d === 20) { returnColor = "purple";
                            } else if (d === 10) { returnColor = "red"; }
                            return returnColor;
                        })

// create in different spaces
var spaceCircles = [30, 70, 110];



var d3Selection = d3.select('body').append('svg')
                                .attr('width', 200)
                                .attr('height', 200);

var circles = d3Selection.selectAll('circle')
                        .data(spaceCircles)
                        .enter()
                        .append('circle');

var cricleSelection = circles.attr('cx', function (d){
                                return d;
                            })
                            .attr('cy', function (d){
                                return d
                            })
                            .attr('r', 20)
                            .style('fill', function (d){
                                var returnColor;
                                if (d === 30) { returnColor = "green";
                                } else if (d === 70) { returnColor = "purple";
                                } else if (d === 110) { returnColor = "red"; }
                                return returnColor;
                            });





























































}]);
