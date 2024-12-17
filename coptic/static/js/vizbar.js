function add_titles(){
	$(".entity").each(function(){
		ident = $(this).find( "a.wikify" );
		if (ident.length>0){
			$(this).prop('title',$(ident[0]).attr('title'));
		}else{
			$(this).prop('title',$(this).attr('entity_type'));
		}
	});
}

function toggle_display(target){
	
		classes = {"entity":["entity","wikify","named","identity"],
						"identity":["wikify","named","identity"],
						"pos":["pos"],
						"translation":["translation"],
						"page":["page"],
						"chapter":["chapter"],
						"verse":["verse"],
						"seg": ["norm"]
						};

		bound_groups = $(".copt_word");
		
		if (target=="coptic"){
			if ($(bound_groups[0]).css("display") == "none"){  // turn on
				$(bound_groups).css("display","inline");
				if ($("#entity_none").prop("checked")){
					toggle_display("entity_none");
				} else if ($("#entity_all").prop("checked")){
					toggle_display("entity_all");
				}
				else {
					toggle_display("entity_types");
				}
				return true;
			} else{ // turn off
				$(bound_groups).css("display","none");
				$(".entity").css("display","none");
				return true;
			}
		}

		if (target=="entity_all"){ // turn on
			for (c of classes["entity"]){
				$(".off_"+c).addClass(c).removeClass("off_" + c).removeClass("off_inline");
				if (target == "pos"){
					$(".entity, .wikify").removeClass("off_4px");
				}
			}
			if ($(bound_groups[0]).css("display") != "none"){  // reveal entities unless Coptic text is hidden
				$(".entity").css("display","inline-block");
			}
			return true;
		} else if (target=="entity_none"){
			for (c of classes["entity"]){
				if ($("." + c).length>0){  // turn off
					$("." + c).addClass("off_" + c).removeClass(c).addClass("off_inline");
				}			
			}
			return true;
		} else if (target=="entity_types"){
			toggle_display("entity_all");
			if ($(bound_groups[0]).css("display") != "none"){  // reveal entities unless Coptic text is hidden
				$(".entity").css("display","inline-block");
			}
			toggle_display("identity");
			return true;
		}
	
		for (c of classes[target]){
			if (target=="seg"){
				$(".norm").addClass("off_seg");
			}
			else{
				if ($("." + c).length>0){  // turn off
					$("." + c).addClass("off_" + c).removeClass(c).addClass("off_inline");
					if (target == "pos"){
						$(".entity, .wikify").addClass("off_4px");
					}
				} else{ // turn on
					$(".off_"+c).addClass(c).removeClass("off_" + c).removeClass("off_inline");
					if (target == "pos"){
						$(".entity, .wikify").removeClass("off_4px");
					}
				}
			}
		}
	}
