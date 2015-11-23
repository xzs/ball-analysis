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


// create the svg element
var d3Selection = d3.select('body').append('svg')
                                .attr('width', 200)
                                .attr('height', 200);

// use data binding to append the circle elements
var circles = d3Selection.selectAll('circle')
                        .data(spaceCircles)
                        .enter()
                        .append('circle');

// set properties for the circle
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




var jsonCircles = [
  {
   "x_axis": 30,
   "y_axis": 30,
   "radius": 20,
   "color" : "green"
  }, {
   "x_axis": 70,
   "y_axis": 70,
   "radius": 20,
   "color" : "purple"
  }, {
   "x_axis": 110,
   "y_axis": 100,
   "radius": 20,
   "color" : "red"
}];


var d3Selection = d3.select('body').append('svg')
                                    .attr('height', 200)
                                    .attr('width', 200);

var circleSelection = d3Selection.selectAll('circle')
                                    .data(jsonCircles)
                                    .enter()
                                    .append('circle');

var circles = circleSelection.attr('cx', function(d){
                                    return d.x_axis;
                                })
                                .attr('cy', function(d){
                                    return d.y_axis;
                                })
                                .attr('r', function(d){
                                    return d.radius;
                                })
                                .style('fill', function(d){
                                    return d.color;
                                })



// when drawing lines and such we can think of it as a pen on paper
// specifiy where the pen will drop (m) and the draw line to (l)
// to draw a line in d3 we can use the d3.svg.line() function

//The data for our line
var lineData = [ { "x": 1,   "y": 5},  { "x": 20,  "y": 20},
                 { "x": 40,  "y": 10}, { "x": 60,  "y": 40},
                 { "x": 80,  "y": 5},  { "x": 100, "y": 60}];

//This is the accessor function we talked about above
// set the coordatines with the x and y values then interpolate the line as linear between the points
var lineFunction = d3.svg.line()
                         .x(function(d) { return d.x; })
                         .y(function(d) { return d.y; })
                         .interpolate("linear");

//The SVG Container
var svgContainer = d3.select("body").append("svg")
                                    .attr("width", 200)
                                    .attr("height", 200);

//The line SVG Path we draw
// <path d="M1,5L20,20L40,10L60,40L80,5L100,60" stroke="blue" stroke-width="2" fill="none"></path>
var lineGraph = svgContainer.append("path")
                            .attr("d", lineFunction(lineData))
                            .attr("stroke", "blue")
                            .attr("stroke-width", 2)
                            .attr("fill", "none");












































}]);
