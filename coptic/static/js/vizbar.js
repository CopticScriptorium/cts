function add_titles() {
  document.querySelectorAll(".entity").forEach(function(el) {
    const ident = el.querySelectorAll("a.wikify");
    if (ident.length > 0) {
      el.title = ident[0].getAttribute('title');
    } else {
      el.title = el.getAttribute('entity_type');
    }
  });
}

function toggle_display(target) {
  const classes = {
    "entity": ["entity", "wikify", "named", "identity"],
    "identity": ["wikify", "named", "identity"], 
    "pos": ["pos"],
    "translation": ["translation"],
    "page": ["page"],
    "chapter": ["chapter"],
    "verse": ["verse"],
    "seg": ["norm"]
  };

  const bound_groups = document.querySelectorAll(".copt_word");

  if (target == "coptic") {
    if (bound_groups[0].style.display == "none") { // turn on
      bound_groups.forEach(el => el.style.display = "inline");
      if (document.getElementById("entity_none").checked) {
        toggle_display("entity_none");
      } else if (document.getElementById("entity_all").checked) {
        toggle_display("entity_all");
      } else {
        toggle_display("entity_types");
      }
      return true;
    } else { // turn off
      bound_groups.forEach(el => el.style.display = "none");
      document.querySelectorAll(".entity").forEach(el => el.style.display = "none");
      return true;
    }
  }

  if (target == "entity_all") { // turn on
    for (const c of classes["entity"]) {
      document.querySelectorAll(".off_" + c).forEach(el => {
        el.classList.add(c);
        el.classList.remove("off_" + c);
        el.classList.remove("off_inline");
      });
      if (target == "pos") {
        document.querySelectorAll(".entity, .wikify").forEach(el => el.classList.remove("off_4px"));
      }
    }
    if (bound_groups[0].style.display != "none") { // reveal entities unless Coptic text is hidden
      document.querySelectorAll(".entity").forEach(el => el.style.display = "inline-block");
    }
    return true;
  } else if (target == "entity_none") {
    for (const c of classes["entity"]) {
      document.querySelectorAll("." + c).forEach(el => {
        el.classList.add("off_" + c);
        el.classList.remove(c);
        el.classList.add("off_inline");
      });
    }
    return true;
  } else if (target == "entity_types") {
    toggle_display("entity_all");
    if (bound_groups[0].style.display != "none") { // reveal entities unless Coptic text is hidden
      document.querySelectorAll(".entity").forEach(el => el.style.display = "inline-block");
    }
    toggle_display("identity");
    return true;
  }

  for (const c of classes[target]) {
    if (target == "seg") {
      document.querySelectorAll(".norm").forEach(el => el.classList.add("off_seg"));
    } else {
      const elements = document.querySelectorAll("." + c);
      if (elements.length > 0) { // turn off
        elements.forEach(el => {
          el.classList.add("off_" + c);
          el.classList.remove(c);
          el.classList.add("off_inline");
        });
        if (target == "pos") {
          document.querySelectorAll(".entity, .wikify").forEach(el => el.classList.add("off_4px"));
        }
      } else { // turn on
        document.querySelectorAll(".off_" + c).forEach(el => {
          el.classList.add(c);
          el.classList.remove("off_" + c);
          el.classList.remove("off_inline");
        });
        if (target == "pos") {
          document.querySelectorAll(".entity, .wikify").forEach(el => el.classList.remove("off_4px"));
        }
      }
    }
  }
}
