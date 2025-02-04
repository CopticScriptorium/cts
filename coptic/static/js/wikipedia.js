const WIKIPEDIA = (function() {
  const my = {};

  // DBPedia SPARQL endpoint
  my.endpoint = 'https://dbpedia.org/sparql/';

  // ### getData
  //
  // Return structured information (via callback) on the provided Wikipedia URL by querying
  // the DBPedia SPARQL endpoint and then tidying the data up.
  //
  // @param: wikipediaUrlOrPageName. A wikipedia URL or pageName or an object
  // with following struture:
  //
  //     {
  //       url: wikipediaURLOrPageName,
  //       raw: false // do not include the raw data in what is returned
  //     }
  //
  // @return: Data is return in the form of the following hash:
  //
  //    {
  //      raw: the-raw-json-from-dbpedia,
  //      summary: a-cleaned-up-set-of-the-properties (see extractSummary),
  //      dbpediaUrl: dbpedia-resource-url e.g. https://dbpedia.org/resource/World_War_II
  //    }
  //
  // Function is asynchronous as we have to call out to DBPedia to get the
  // info.
  my.getData = function(wikipediaUrlOrPageName, callback, error) {
    const url = my._getDbpediaUrl(wikipediaUrlOrPageName);
    function onSuccess(data) {
      const out = {
        raw: data,
        dbpediaUrl: url,
        summary: null
      };
      if (data) {
        out.summary = my.extractSummary(url, data);
      } else {
        out.error = 'Failed to retrieve data. Is the URL or page name correct?';
      }
      callback(out);
    }
    my.getRawJson(url, onSuccess, error);
  };

  // ### _getDbpediaUrl
  //
  // Convert the incoming URL or page name to a DBPedia url
  my._getDbpediaUrl = function(url) {
    if (url.indexOf('wikipedia')!=-1) {
      const parts = url.split('/');
      const title = parts[parts.length-1];
      url = 'https://dbpedia.org/resource/' + title;
      return url;
    } else if (url.indexOf('dbpedia.org')!=-1) {
      return url;
    } else {
      url = 'https://dbpedia.org/resource/' + url.replace(/ /g, '_');
      return url;
    }
  };

  // ### getRawJson
  //
  // get raw RDF JSON for DBPedia resource from DBPedia SPARQL endpoint
  my.getRawJson = function(url, callback, error) {
    const sparqlQuery = 'DESCRIBE <{{url}}>'.replace('{{url}}', url);
    fetch(my.endpoint + '?' + new URLSearchParams({
      query: sparqlQuery,
      format: 'application/rdf+json'
    }))
    .then(response => response.json())
    .then(callback)
    .catch(error);
  };

  // Standard RDF namespace prefixes for use in lookupProperty function
  my.PREFIX = {
    rdf: "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    rdfs: "http://www.w3.org/2000/01/rdf-schema#",
    xsd: "http://www.w3.org/2001/XMLSchema#",
    owl: "http://www.w3.org/2002/07/owl#",
    dc: "http://purl.org/dc/terms/",
    foaf: "http://xmlns.com/foaf/0.1/",
    vcard: "http://www.w3.org/2006/vcard/ns#",
    dbp: "http://dbpedia.org/property/",
    dbo: "http://dbpedia.org/ontology/",
    geo: "http://www.geonames.org/ontology#",
    wgs: "http://www.w3.org/2003/01/geo/wgs84_pos#"
  };

  my._expandNamespacePrefix = function(uriWithPrefix) {
    for(const key in WIKIPEDIA.PREFIX) {
      if (uriWithPrefix.indexOf(key + ':') === 0) {
        uriWithPrefix = WIKIPEDIA.PREFIX[key] + uriWithPrefix.slice(key.length + 1);
      }
    }
    return uriWithPrefix;
  };

  // ### lookupProperty
  // 
  // lookup a property value given a standard RDF/JSON property dictionary
  // e.g. something like ...
  // 
  //       ...
  //       "http://dbpedia.org/property/regent": [
  //              {
  //                  "type": "uri",
  //                  "value": "http://dbpedia.org/resource/Richard_I_of_England"
  //              }
  //          ],
  //       ...
  my._lookupProperty = function(dict, property) {
    property = my._expandNamespacePrefix(property);
    const values = dict[property];
    for (const idx in values) {
      // only take english values if lang is present
      if (!values[idx]['lang'] || values[idx].lang == 'en') {
        return values[idx].value;
      }
    }
  };

  // Extract a standard set of attributes (e.g. title, description, dates etc
  // etc) from rdfJson and the given subject uri (url) e.g.
  // 
  //      extractSummary('http://dbpedia.org/resource/Rufus_Pollock', rdfJson object from dbpedia)
  my.extractSummary = function(subjectUri, rdfJson) {
    const properties = rdfJson[subjectUri];
    function lkup(attribs) {
      if (attribs instanceof Array) {
        const out = [];
        for (const idx in attribs) {
          const _tmp = my._lookupProperty(properties, attribs[idx]);
          if (_tmp) {
            out.push(_tmp);
          }
        }
        return out;
      } else {
        return my._lookupProperty(properties, attribs);
      }
    }

    const summaryInfo = {
      title: lkup('rdfs:label'),
      description: lkup('dbo:abstract'),
      summary: lkup('rdfs:comment'),
      startDates: lkup(['dbo:birthDate', 'dbo:formationDate', 'dbo:foundingYear']),
      endDates: lkup('dbo:deathDate'),
      // both dbp:date and dbo:date are usually present but dbp:date is
      // frequently "bad" (e.g. just a single integer rather than a date)
      // whereas ontology value is better
      date: lkup('dbo:date'),
      place: lkup('dbp:place'),
      birthPlace: lkup('dbo:birthPlace'),
      deathPlace: lkup('dbo:deathPlace'),
      source: lkup('foaf:page'),
      images: lkup(['dbo:thumbnail', 'foaf:depiction', 'foaf:img']),
      location: {
        lat: lkup('wgs:lat'),
        lon: lkup('wgs:long')
      },
      types: [],
      type: null
    };

    // getLastPartOfUrl
    function gl(url) {
      const parts = url.split('/');
      return parts[parts.length-1];
    }

    const typeUri = my._expandNamespacePrefix('rdf:type');
    const types = [];
    const typeObjs = properties[typeUri];
    for(const idx in typeObjs) {
      const value = typeObjs[idx].value;
      // let's be selective
      // ignore yago and owl stuff
      if (value.indexOf('dbpedia.org/ontology') != -1 || value.indexOf('schema.org') != -1 || value.indexOf('foaf/0.1') != -1) {
        // TODO: ensure uniqueness (do not push same thing ...)
        summaryInfo.types.push(gl(value));
        // use schema.org value as the default
        if (value.indexOf('schema.org') != -1) {
          summaryInfo.type = gl(value);
        }
      }
    }
    if (!summaryInfo.type && summaryInfo.types.length > 0) {
      summaryInfo.type = summaryInfo.types[0];
    }

    summaryInfo.start = summaryInfo.startDates.length > 0 ? summaryInfo.startDates[0] : summaryInfo.date;
    summaryInfo.end = summaryInfo.endDates;
    if (!summaryInfo.place) {
      // death place is more likely more significant than death place
      summaryInfo.place = summaryInfo.deathPlace || summaryInfo.birthPlace;
    }
    // if place a uri clean it up ...
    if (summaryInfo.place) {
      summaryInfo.place = gl(summaryInfo.place);
    }
    summaryInfo.location.title = summaryInfo.place;
    summaryInfo.image = summaryInfo.images ? summaryInfo.images[0] : null;

    return summaryInfo;
  };

  // Function to display Wikipedia information
  my.wikipop = function(e, article_title) {
    const target = e.target;
    const position = {
      top: target.getBoundingClientRect().top + window.scrollY - 3,
      left: target.getBoundingClientRect().left + window.scrollX
    };

    const infobox = document.getElementById("infobox");
    
    // Set fixed dimensions before displaying content
    infobox.style.width = "60%"; // Set a fixed width
    infobox.style.minWidth = "200px"; // Set a fixed width
    infobox.style.minHeight = "300px"; // Set a max height
    infobox.style.height = "fit-content"; // Set a max height
    infobox.style.overflowY = "auto"; // Allow vertical scrolling if needed
    
    // clear box
    document.querySelector('.thumbnail').style.display = "none";
    document.querySelector('.summary').textContent = "";
    document.querySelector('.title').innerHTML = `<h4>${article_title}</h4><span> (<a href="https://en.wikipedia.org/wiki/${article_title.replace(/ /g, "_")}" target="_blank">open in Wikipedia</a>)</span>`;

    infobox.style.display = "block";
    infobox.style.top = position.top + 'px';
    infobox.style.left = position.left + 'px';

    // Remove previous event listeners to prevent duplicates
    const newInfobox = infobox.cloneNode(true);
    infobox.parentNode.replaceChild(newInfobox, infobox);
    
    // Add event listeners
    let hideTimeout;
    newInfobox.addEventListener("mouseout", function(e) {
      // Check if the mouse is really leaving the infobox (not moving to a child element)
      if (!newInfobox.contains(e.relatedTarget)) {
        hideTimeout = setTimeout(my.hide_wiki, 300); // Add small delay before hiding
      }
    });
    
    newInfobox.addEventListener("mouseover", function() {
      if (hideTimeout) {
        clearTimeout(hideTimeout); // Cancel hiding if mouse returns
      }
    });

    document.querySelectorAll(".index-list, .meta-value, .index-annis, h1").forEach(el => {
      el.addEventListener("mouseover", my.hide_wiki);
    });

    article_title = "https://en.wikipedia.org/wiki/" + article_title.replace(/ /g, "_");
    document.querySelector('.summary').textContent = ""; // pre-emptively prepare missing entry response

    const display = function(info) {
      if (!info) {
        document.querySelector('.summary').textContent = "[No Wikidata entry found for this entity]";
        return true;
      }
      const rawData = info.raw;
      const summaryInfo = info.summary;
      const properties = rawData[info.dbpediaUrl];

      document.querySelector('.title').innerHTML = `<h4>${summaryInfo.title}</h4><span> (<a href="${article_title}" target="_blank">open in Wikipedia</a>)</span>`;

      if (summaryInfo.summary) {
        document.querySelector('.summary').textContent = summaryInfo["summary"];
      } else {
        document.querySelector('.summary').textContent = "[No Wikidata entry found for this entity]";
        return true;
      }

      if (summaryInfo.image) {
        const thumbnail = document.querySelector('.thumbnail');
        thumbnail.src = summaryInfo.image;
        thumbnail.style.display = "inline-block";
      }

      const map = document.getElementById("map");
      map.style.display = "none";
      const special_meta = "people";
      if ('location' in summaryInfo) {
        if ('lat' in summaryInfo["location"] && 'lon' in summaryInfo["location"]) {
          const lon = summaryInfo["location"].lon;
          const lat = summaryInfo["location"].lat;
          if (lon && lat && special_meta == 'places') {
            const map_url = `https://maps.google.com/maps?q=${lat},${lon}`;
            map.innerHTML = `<a href="${map_url}"><i class="fa fa-map-marker"></i> Map</a>`;
            map.style.display = "inline-block";
          }
        }
      }
    };

    my.getData(article_title, display, function(error) {
      console.log(error);
    });
  };

  my.hide_wiki = function() {
    document.getElementById("infobox").style.display = "none";
  };

  // Ensure the functions are called after the page content is loaded
  document.addEventListener('DOMContentLoaded', function() {
    // Example usage: Attach wikipop to elements with class 'wiki-link'
    document.querySelectorAll('.wiki-link').forEach(el => {
      el.addEventListener('mouseover', function(e) {
        const article_title = this.dataset.title;
        my.wikipop(e, article_title);
      });
    });
  });

  return my;
})();