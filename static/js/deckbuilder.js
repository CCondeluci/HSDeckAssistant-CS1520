// Main Deckbuilder Javascript

//list.js initialization
var options = {
    valueNames: [ 'name','type','cost','rarity','race','artist','cardset','mechanics' ]
};

var testList = new List('deckbuilder', options);

// Load XML Mapping for tooltips
if (window.XMLHttpRequest) {
   xhttp = new XMLHttpRequest();
} else {    // IE 5/6
   xhttp = new ActiveXObject("Microsoft.XMLHTTP");
}

xhttp.open("GET", "/static/CARD.xml", false);
xhttp.send();
xmlDoc = xhttp.responseXML;

$("form").keypress(function(e) {
  //Enter key
  if (e.which == 13) {
    return false;
  }
});

// "Define" objects that will be used in functions
var deck_list = {
	list: [],
	decksize: 0,
	dustcost: 0,
	deckname: "",
	deck_class: "",
	write_up: "",
	curve: [0,0,0,0,0,0,0,0]
};

var d_card = {

	cardName: "",
	count: 0,
	rarity: 0,
	cardId: "",
	imgurl: "",
	cardSet: "",
	mana: 0,
	hheadID: ""
};

//Submission flag
var flag = 0;

//Gets the class name
function getQueryVariable(variable) {
  var query = window.location.search.substring(1);
  var vars = query.split("&");
  for (var i=0;i<vars.length;i++) {
    var pair = vars[i].split("=");
    if (pair[0] == variable) {
      return pair[1];
    }
  } 
}

//Sends ajax request that adds deck to ndb
function PrepareDeck(){

	if( flag > 0 )
		return false;

	sortDeckList();
	checkDeckSize();
	checkDeckCost();
	
	if(deck_list.decksize < 30){
		alert("You cannot save a deck smaller than 30 cards!");
		return false;
	}
	else if(deck_list.deckname == "Enter Deck Name Here..." || deck_list.deckname == ""){
		alert("You cannot save a deck without a name!");
		return false;
	}
	else {
		deck_list.deck_class = getQueryVariable("class");
		// deck_list.write_up = document.getElementById('writeupbody').innerHTML;
		deck_list.write_up = $("#txtEditor").Editor("getText");
		$test = JSON.stringify(deck_list);

		$.ajax({

			type: "POST",
			url: "/savedeck",
			data: {inputData: $test}

		}).done(function(data){
			console.log(data);
		});

		document.forms['decklist_saver_form'].submit();

		flag++;
	}
}

//constructor for a card in a decklist
function make_dcard(card) {

	var new_dcard = new Object();
	new_dcard.cardName = card.getAttribute('cardName');
	new_dcard.count = 1;
	new_dcard.rarity = card.getAttribute('rarity');
	new_dcard.cardId = card.getAttribute('cardId');
	new_dcard.imgurl = card.getAttribute('imgurl');
	new_dcard.cardSet = card.getAttribute('cardSet');
	new_dcard.mana = card.getAttribute('cost');

	return new_dcard;
}

//Add card to the decklist, both visually and on backend
function addCard(card) {

	sortDeckList();

	var main_list = document.getElementById('inner_list');
	var current_dcard = make_dcard(card);
	var index = deck_list.list.map(function(e) { return e.cardName; }).indexOf(current_dcard.cardName);

	//alert(index);

	if( index == -1 && deck_list.decksize < 30){
		deck_list.list.push(current_dcard);
		deck_list.decksize++;
		deck_list.dustcost += getCardDust(current_dcard);

		if(current_dcard.mana >= 7)
			deck_list.curve[7] += 1;
		else
			deck_list.curve[current_dcard.mana] += 1;

	}
	else if (index >= 0 && deck_list.list[index].count < 2 && deck_list.decksize < 30 && current_dcard.rarity != "Legendary") {
		deck_list.list[index].count += 1;
		current_dcard = deck_list.list[index];
		deck_list.decksize++;
		deck_list.dustcost += getCardDust(current_dcard);

		if(current_dcard.mana >= 7)
			deck_list.curve[7] += 1;
		else
			deck_list.curve[current_dcard.mana] += 1;
	}
	else {
		current_dcard = deck_list.list[index];
	}

	sortDeckList();
	index = deck_list.list.map(function(e) { return e.cardName; }).indexOf(current_dcard.cardName);

	var existCheck = document.getElementById(current_dcard.cardId);

    
	if( existCheck == null ){

	 	var path_drill = '//Card[a = \'' + current_dcard.cardId + '\']/h';
		var hheadID_url = xmlDoc.evaluate(path_drill, xmlDoc, null, XPathResult.STRING_TYPE, null).stringValue;
		current_dcard.hheadID = hheadID_url;

		$("#inner_list li").eq(index).after("<li id=\"" + current_dcard.cardId + "\" onclick=\"removeCard(this)\" class=\"" + current_dcard.rarity + "\"><a onclick=\"return false;\" id=\"tooltip-container\" href=\"http://www.hearthhead.com/card=" + hheadID_url +"\"><div class=\"deckcardimage\" style=\"background-image: url('" + card.getAttribute('imgurl') + "');\"></div>" + "<div class=\"content\"> <div class=\"mana\">" + current_dcard.mana + "</div><div class=\"deckcardname\">" + current_dcard.cardName + "</div><div class=\"spacer\"></div><div class=\"cardcount\">" + current_dcard.count + "</div>\n</div>\n</a></li>");
	}
	else {
		var card_count = document.getElementById(current_dcard.cardId).childNodes[0].childNodes[1].childNodes[4];

		if( current_dcard.count <= 2 && current_dcard.rarity != "Legendary"){
			card_count.innerHTML = current_dcard.count;
		}
	}

	checkDeckSize();
	checkDeckCost();
	return false;
}

//Remove a card from the decklist, both visually and on backend
function removeCard(card) {

	var main_list = document.getElementById('inner_list');
	var card_id = document.getElementById(card.getAttribute('id'));
	var card_count = card_id.childNodes[0].childNodes[1].childNodes[4];

	var index = deck_list.list.map(function(e) { return e.cardId; }).indexOf(card.getAttribute('id'));

	if( card_count.innerHTML == 2 ){
		deck_list.list[index].count = 1;
		card_count.innerHTML = 1;
		deck_list.decksize--;
		deck_list.dustcost -= getCardDust(deck_list.list[index]);

		if(deck_list.list[index].mana >= 7)
			deck_list.curve[7] -= 1;
		else
			deck_list.curve[deck_list.list[index].mana] -= 1;
	}
	else {
		deck_list.dustcost -= getCardDust(deck_list.list[index]);

		if(deck_list.list[index].mana >= 7)
			deck_list.curve[7] -= 1;
		else
			deck_list.curve[deck_list.list[index].mana] -= 1;

		deck_list.list.splice(index, 1);
		main_list.removeChild(card_id);
		deck_list.decksize--;

		var leftoverTooltip = document.getElementsByClassName("wowhead-tooltip hearthhead-tooltip-image");
		if(leftoverTooltip)
			leftoverTooltip[0].setAttribute('style', 'position: absolute; top: 251px; left: 221px; width: 200px; visibility: hidden; display: none;');
		leftoverTooltip = document.getElementsByClassName("wowhead-tooltip");
		if(leftoverTooltip)
			leftoverTooltip[0].setAttribute('style', 'position: absolute; top: -2323px; left: -2323px; width: 0px; display: none; visibility: hidden;');

	}


	sortDeckList();
	checkDeckSize();
	checkDeckCost();
}

//Get the dust cost of a card in the decklist
function getCardDust (card) {
	// body...
	var dust = 0;
	var rarity = card.rarity;

	switch (rarity) {

		case "Free":
			dust = 0;
			break;
		case "Common":
			dust = 40;
			break;
		case "Rare":
			dust = 100;
			break;
		case "Epic":
			dust = 400;
			break;
		case "Legendary":
			dust = 1600;
			break;
		default:
			dust = 0;
	}

	//Some cardsets have no cost regardless of rarity
	if( card.cardSet == "Basic" )
		dust = 0;
	else if( card.cardSet == "Blackrock Mountain" )
		dust = 0;
	else if( card.cardSet == "Naxxramas" )
		dust = 0;

	return dust;
}

//Updates deck size
function checkDeckSize() {
	// body...
	var viewsize = document.getElementById('cardcounter');
	viewsize.innerHTML = deck_list.decksize + " / 30";

	//We're also going to do the name here as well
	var temp_name = document.getElementById('deck_name_box').value;
	deck_list.deckname = temp_name;
}

//Updates dust cost
function checkDeckCost() {
	// body...
	var viewdust = document.getElementById('dustcounter');
	viewdust.innerHTML = deck_list.dustcost + " Dust to Craft";

	//Curve handler
	$('[data-bar-chart]').each(function (i, svg) {
		d3.selectAll("svg > *").remove();
	  	var curve = deck_list.curve;
	    var $svg = $(svg);
	    var data = curve.map(function (datum) {
	      return parseFloat(datum);
	    });

	    var barWidth = 29.5;
	    var barSpace = 0.5;
	    var chartHeight = $svg.outerHeight();

	    var y = d3.scale.linear()
	              .domain([0, d3.max(data)])
	              .range([0, chartHeight]);

	    d3.select(svg)
	      .selectAll("rect")
	        .data(data)
	      .enter().append("rect")
	        .attr("class", "bar")
	        .attr("width", barWidth)
	        .attr("x", function (d, i) { return barWidth*i + barSpace*i; })
	        .attr("y", chartHeight)
	        .attr("height", 0)
	        .attr("y", function (d, i) { return chartHeight-y(d); })
	        .attr("height", function (d) { return y(d); });
	 });

}

//Resets the decklist both visually and on the backend
function resetDeck() {
	var main_list = document.getElementById('inner_list');
	main_list.innerHTML = '<li></li>';

	deck_list = {
		list: [],
		decksize: 0,
		dustcost: 0,
		deckname: "",
		deck_class: "",
		write_up: "",
		curve: [0,0,0,0,0,0,0,0]
	};

	checkDeckSize();
	checkDeckCost();
	sortDeckList();
}

//Sort the backend decklist
function sortDeckList() {
	// body...

	deck_list.list = deck_list.list.sort( function(a, b) {
			return parseFloat(a.mana) - parseFloat(b.mana);
		}
	);
}

//Export a deck to Cockatrice format
function exportDeck(w, h) {
	checkDeckSize();
	checkDeckCost();
	sortDeckList();
	var bsPopup = document.getElementById('deckbody')
	bsPopup.innerHTML = "";
	var printdeck = document.createElement('textarea');
	printdeck.setAttribute('rows', 50);
	printdeck.setAttribute('cols', 50);
	printdeck.setAttribute('class', 'exportArea');

	templist = deck_list.list;
	bsPopup.innerHTML = "<p>" + deck_list.deckname + "</p>";

	for( var x = 0; x < templist.length; x++ ) {
		printdeck.innerHTML += templist[x].count + " " + templist[x].cardName + "\n";
	}

	bsPopup.appendChild(printdeck);
}

