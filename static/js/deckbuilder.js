
$(window).load(function() {
	$(".loader").fadeOut("slow");
})

var deck_list = {
	list: [],
	decksize: 0,
	dustcost: 0
};

var d_card = {

	cardName: "",
	count: 0,
	rarity: 0,
	cardId: "",
	imgurl: "",
	cardSet: "",
	mana: 0
};

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
	}
	else if (index >= 0 && deck_list.list[index].count < 2 && deck_list.decksize < 30) {
		deck_list.list[index].count += 1;
		current_dcard = deck_list.list[index];
		deck_list.decksize++;
		deck_list.dustcost += getCardDust(current_dcard);
	}
	else {
		current_dcard = deck_list.list[index];
	}

	sortDeckList();
	index = deck_list.list.map(function(e) { return e.cardName; }).indexOf(current_dcard.cardName);

	//alert(JSON.stringify(deck_list));
	var existCheck = document.getElementById(current_dcard.cardId);

	if( existCheck == null ){

	    // alert(testxml);
	    var path_drill = '//Card[api_id = \'' + current_dcard.cardId + '\']/hearthhead_id';
		var hheadID_url = card.getAttribute('href');

		// var firstAdd = document.createElement('li');
		// firstAdd.setAttribute('id', current_dcard.cardId);
		// firstAdd.setAttribute('onclick', 'removeCard(this)');
		// firstAdd.setAttribute('class', current_dcard.rarity);
		// firstAdd.innerHTML += "<a onclick=\"return false;\" id=\"tooltip-container\" href=\"" + hheadID_url +"\"><div class=\"deckcardimage\" style=\"background-image: url('" + card.getAttribute('imgurl') + "');\"></div>" + "<div class=\"content\"> <div class=\"mana\">" + current_dcard.mana + "</div><div class=\"deckcardname\">" + current_dcard.cardName + "</div><div class=\"spacer\"></div><div class=\"cardcount\">" + current_dcard.count + "</div>\n</div>\n</a>";

		// main_list.appendChild(firstAdd);

		//alert(index);
		$("#inner_list li").eq(index).after("<li id=\"" + current_dcard.cardId + "\" onclick=\"removeCard(this)\" class=\"" + current_dcard.rarity + "\"><a onclick=\"return false;\" id=\"tooltip-container\" href=\"" + hheadID_url +"\"><div class=\"deckcardimage\" style=\"background-image: url('" + card.getAttribute('imgurl') + "');\"></div>" + "<div class=\"content\"> <div class=\"mana\">" + current_dcard.mana + "</div><div class=\"deckcardname\">" + current_dcard.cardName + "</div><div class=\"spacer\"></div><div class=\"cardcount\">" + current_dcard.count + "</div>\n</div>\n</a></li>");
	}
	else {
		var card_count = document.getElementById(current_dcard.cardId).childNodes[0].childNodes[1].childNodes[4];

		if( current_dcard.count <= 2 && current_dcard.rarity != "Legendary" ){
			card_count.innerHTML = current_dcard.count;
		}
	}

	checkDeckSize();
	checkDeckCost();
	return false;
}

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
	}
	else {
		deck_list.dustcost -= getCardDust(deck_list.list[index]);
		deck_list.list.splice(index, 1);
		main_list.removeChild(card_id);
		deck_list.decksize--;
	}

	sortDeckList();
	checkDeckSize();
	checkDeckCost();
}

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

	if( card.cardSet == "Basic" )
		dust = 0;
	else if( card.cardSet == "Blackrock Mountain" )
		dust = 0;
	else if( card.cardSet == "Naxxramas" )
		dust = 0;

	return dust;
}

function checkDeckSize() {
	// body...
	var viewsize = document.getElementById('cardcounter');
	viewsize.innerHTML = deck_list.decksize + " / 30";
}

function checkDeckCost() {
	// body...
	var viewdust = document.getElementById('dustcounter');
	viewdust.innerHTML = deck_list.dustcost + " Dust to Craft";
}

function resetDeck() {
	var main_list = document.getElementById('inner_list');
	main_list.innerHTML = '<li></li>';

	deck_list = {
		list: [],
		decksize: 0,
		dustcost: 0
	};

	checkDeckSize();
	checkDeckCost();
	sortDeckList();
}

function sortDeckList() {
	// body...

	deck_list.list = deck_list.list.sort( function(a, b) {
			return parseFloat(a.mana) - parseFloat(b.mana);
		}
	);
}

function exportDeck(w, h) {
	sortDeckList();
	var left = (screen.width/2)-(w/2);
		var top = (screen.height/2)-(h/2);
		var myWindow = window.open("", "Deck Export", 'toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=no, resizable=no, copyhistory=no, width='+w+', height='+h+', top='+top+', left='+left);
	var printdeck = myWindow.document.createElement('textarea');
	printdeck.setAttribute('rows', 30);
	printdeck.setAttribute('cols', 50);

	templist = deck_list.list;

	for( var x = 0; x < templist.length; x++ ) {
		printdeck.innerHTML += templist[x].count + " " + templist[x].cardName + "\n";
	}

	myWindow.document.body.appendChild(printdeck);
}