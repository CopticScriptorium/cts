// config.js
const CONFIG = {
  ENDPOINT: 'https://dbpedia.org/sparql/',
  PREFIX: {
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
  }
};

// Custom error class
class WikipediaError extends Error {
  constructor(message, originalError = null) {
    super(message);
    this.name = 'WikipediaError';
    this.originalError = originalError;
  }
}

// WikipediaService.js
class WikipediaService {
  constructor(endpoint = CONFIG.ENDPOINT) {
    this.endpoint = endpoint;
  }

  // ### getData
  //
  // Return structured information on the provided Wikipedia URL by querying
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
  // @return: Promise that resolves to data in the form:
  //
  //    {
  //      raw: the-raw-json-from-dbpedia,
  //      summary: a-cleaned-up-set-of-the-properties (see extractSummary),
  //      dbpediaUrl: dbpedia-resource-url e.g. http://dbpedia.org/resource/World_War_II
  //    }
  async getData(wikipediaUrlOrPageName) {
    try {
      const url = this._getDbpediaUrl(wikipediaUrlOrPageName);
      const data = await this.getRawJson(url);
      
      return {
        raw: data,
        dbpediaUrl: url,
        summary: data ? this.extractSummary(url, data) : null,
        error: !data ? 'Failed to retrieve data. Is the URL or page name correct?' : null
      };
    } catch (err) {
      throw new WikipediaError('Error fetching Wikipedia data', err);
    }
  }

  // ### _getDbpediaUrl
  //
  // Convert the incoming URL or page name to a DBPedia url
  _getDbpediaUrl(url) {
    if (url.indexOf('wikipedia')!=-1) {
      const parts = url.split('/');
      const title = parts[parts.length-1];
      url = 'http://dbpedia.org/resource/' + title;
      return url;
    } else if (url.indexOf('dbpedia.org')!=-1) {
      return url;
    } else {
      url = 'http://dbpedia.org/resource/' + url.replace(/ /g, '_');
      return url;
    }
  }

  // ### getRawJson
  //
  // get raw RDF JSON for DBPedia resource from DBPedia SPARQL endpoint
  async getRawJson(url) {
    const sparqlQuery = 'DESCRIBE <{{url}}>'.replace('{{url}}', url);
    try {
      const response = await fetch(this.endpoint + '?' + new URLSearchParams({
        query: sparqlQuery,
        format: 'application/rdf+json'
      }));
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (err) {
      console.error('Error fetching RDF JSON:', err);
      throw err;
    }
  }

  _expandNamespacePrefix(uriWithPrefix) {
    for(const key in CONFIG.PREFIX) {
      if (uriWithPrefix.indexOf(key + ':') === 0) {
        uriWithPrefix = CONFIG.PREFIX[key] + uriWithPrefix.slice(key.length + 1);
      }
    }
    return uriWithPrefix;
  }

  // ### lookupProperty
  // 
  // lookup a property value given a standard RDF/JSON property dictionary
  _lookupProperty(dict, property) {
    property = this._expandNamespacePrefix(property);
    const values = dict[property];
    for (const idx in values) {
      // only take english values if lang is present
      if (!values[idx]['lang'] || values[idx].lang == 'en') {
        return values[idx].value;
      }
    }
  }

  // Helper method to handle property lookups
  _lookupProperties(properties, propertyNames) {
    if (Array.isArray(propertyNames)) {
      return propertyNames
        .map(prop => this._lookupProperty(properties, prop))
        .filter(Boolean);
    }
    return this._lookupProperty(properties, propertyNames);
  }

  // Extract a standard set of attributes from rdfJson
  extractSummary(subjectUri, rdfJson) {
    const properties = rdfJson[subjectUri];
    const lookup = props => this._lookupProperties(properties, props);

    const summary = {
      title: lookup('rdfs:label'),
      description: lookup('dbo:abstract'),
      summary: lookup('rdfs:comment'),
      dates: {
        start: lookup(['dbo:birthDate', 'dbo:formationDate', 'dbo:foundingYear']),
        end: lookup('dbo:deathDate'),
        general: lookup('dbo:date')
      },
      place: lookup('dbp:place'),
      birthPlace: lookup('dbo:birthPlace'),
      deathPlace: lookup('dbo:deathPlace'),
      source: lookup('foaf:page'),
      images: lookup(['dbo:thumbnail', 'foaf:depiction', 'foaf:img']),
      location: {
        lat: lookup('wgs:lat'),
        lon: lookup('wgs:long')
      },
      types: [],
      type: null
    };

    function gl(url) {
      const parts = url.split('/');
      return parts[parts.length-1];
    }

    const typeUri = this._expandNamespacePrefix('rdf:type');
    const typeObjs = properties[typeUri];
    for(const idx in typeObjs) {
      const value = typeObjs[idx].value;
      if (value.indexOf('dbpedia.org/ontology') != -1 || value.indexOf('schema.org') != -1 || value.indexOf('foaf/0.1') != -1) {
        summary.types.push(gl(value));
        if (value.indexOf('schema.org') != -1) {
          summary.type = gl(value);
        }
      }
    }
    if (!summary.type && summary.types.length > 0) {
      summary.type = summary.types[0];
    }

    summary.start = summary.dates.start.length > 0 ? summary.dates.start[0] : summary.dates.general;
    summary.end = summary.dates.end;
    if (!summary.place) {
      summary.place = summary.deathPlace || summary.birthPlace;
    }
    if (summary.place) {
      summary.place = gl(summary.place);
    }
    summary.location.title = summary.place;
    summary.image = summary.images ? summary.images[0] : null;

    return this._enrichSummary(summary);
  }

  _enrichSummary(summary) {
    // Implementation of _enrichSummary method
    return summary;
  }
}

// UI Handler class
class WikipediaPopup {
  constructor(selector = '.wiki-link') {
    this.wikiService = new WikipediaService();
    this.selector = selector;
    this.hideTimeout = null;
    this.setupEventListeners();
  }

  setupEventListeners() {
    document.addEventListener('DOMContentLoaded', () => {
      document.querySelectorAll(this.selector).forEach(el => {
        el.addEventListener('mouseover', (e) => {
          const articleTitle = el.dataset.title;
          this.show(e, articleTitle);
          console.log(articleTitle);
        });
      });
    });
  }

  async show(e, articleTitle) {
    const target = e.target;
    const position = {
      top: target.getBoundingClientRect().top + window.scrollY - 3,
      left: target.getBoundingClientRect().left + window.scrollX
    };

    const infobox = document.getElementById("infobox");
    
    // Set fixed dimensions before displaying content
    infobox.style.width = "60%";
    infobox.style.minWidth = "200px";
    infobox.style.minHeight = "300px";
    infobox.style.height = "fit-content";
    infobox.style.overflowY = "auto";
    
    // clear box
    document.querySelector('.thumbnail').style.display = "none";
    document.querySelector('.summary').textContent = "";
    document.querySelector('.title').innerHTML = `<h4>${articleTitle}</h4><span> (<a href="https://en.wikipedia.org/wiki/${articleTitle.replace(/ /g, "_")}" target="_blank">open in Wikipedia</a>)</span>`;

    infobox.style.display = "block";
    infobox.style.top = position.top + 'px';
    infobox.style.left = position.left + 'px';

    // Remove previous event listeners to prevent duplicates
    const newInfobox = infobox.cloneNode(true);
    infobox.parentNode.replaceChild(newInfobox, infobox);
    
    // Add event listeners
    let hideTimeout;
    newInfobox.addEventListener("mouseout", function(e) {
      if (!newInfobox.contains(e.relatedTarget)) {
        hideTimeout = setTimeout(this.hide_wiki, 300);
      }
    }.bind(this));
    
    newInfobox.addEventListener("mouseover", function() {
      if (hideTimeout) {
        clearTimeout(hideTimeout);
      }
    });

    document.querySelectorAll(".index-list, .meta-value, .index-annis, h1").forEach(el => {
      el.addEventListener("mouseover", this.hide_wiki);
    });

    articleTitle = "https://en.wikipedia.org/wiki/" + articleTitle.replace(/ /g, "_");
    document.querySelector('.summary').textContent = "";

    try {
      const info = await this.wikiService.getData(articleTitle);
      
      if (!info) {
        document.querySelector('.summary').textContent = "[No Wikidata entry found for this entity]";
        return;
      }

      const summaryInfo = info.summary;

      document.querySelector('.title').innerHTML = `<h4>${summaryInfo.title}</h4><span> (<a href="${articleTitle}" target="_blank">open in Wikipedia</a>)</span>`;

      if (summaryInfo.summary) {
        document.querySelector('.summary').textContent = summaryInfo.summary;
      } else {
        document.querySelector('.summary').textContent = "[No Wikidata entry found for this entity]";
        return;
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
        if ('lat' in summaryInfo.location && 'lon' in summaryInfo.location) {
          const {lon, lat} = summaryInfo.location;
          if (lon && lat && special_meta == 'places') {
            const map_url = `https://maps.google.com/maps?q=${lat},${lon}`;
            map.innerHTML = `<a href="${map_url}"><i class="fa fa-map-marker"></i> Map</a>`;
            map.style.display = "inline-block";
          }
        }
      }

    } catch (err) {
      console.error('Error displaying Wikipedia info:', err);
      document.querySelector('.summary').textContent = "Error loading Wikipedia data";
    }
  }

  hide_wiki() {
    document.getElementById("infobox").style.display = "none";
  }
}

// Make classes available globally
window.WikipediaService = WikipediaService;
window.WikipediaPopup = WikipediaPopup;

const wikiPopup = new WikipediaPopup();
console.log(wikiPopup);