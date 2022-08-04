# TidalTime
A simple script to:
1. scrape tidal prediction from BBC
2. save to local db (sqlite)
3. sent Slack notification. 

the tidal.db contains a table with available UK ports (full list below)

Use in conjunction with cronjob
to monitor daily. e.g.:
```
0 4 * * * /home/wei/miniconda3/bin/python /home/wei/TidalTime/tide_time.py -p 104 -p 103
0 21 * * 2,4 /home/wei/miniconda3/bin/python /home/wei/TidalTime/notification.py -c config.cfg -p 103 -p 104 -t 0.5
```

| Location                             | port_id |
|--------------------------------------|---------|
| Aberdaron                            | 482a    |
| Aberdeen                             | 244     |
| Aberdovey                            | 486     |
| Aberporth                            | 488a    |
| Aberystwyth                          | 487     |
| Albert Bridge                        | 114     |
| Aldeburgh                            | 139     |
| Allington Lock                       | 109e    |
| Alloa                                | 229a    |
| Amble                                | 206     |
| Amlwch                               | 477     |
| Annan Waterfoot                      | 426     |
| Anstruther Easter                    | 233     |
| Applecross                           | 338a    |
| Appledore                            | 536     |
| Arbroath                             | 241     |
| Ardchattan Point                     | 371b    |
| Ardnave Point                        | 378     |
| Ardrossan                            | 410     |
| Arrochar                             | 401     |
| Ayr                                  | 413     |
| Badcall Bay                          | 329     |
| Balivanich                           | 318     |
| Baltasound Pier                      | 290b    |
| Banff                                | 247     |
| Barcaldine Pier                      | 370a    |
| Bardsey Island                       | 482     |
| Barmouth                             | 485     |
| Barnstaple                           | 539     |
| Barra (North Bay)                    | 314     |
| Barra Head                           | 316     |
| Barrow (Ramsden Dock)                | 439     |
| Barry                                | 513     |
| Bawdsey                              | 135     |
| Bay Of Laig                          | 354     |
| Bay Of Quendale                      | 296     |
| Bays Loch                            | 310b    |
| Beachley (Aust)                      | 518     |
| Beaumaris                            | 472     |
| Bee Ness                             | 108a    |
| Bembridge Harbour                    | 54      |
| Berkeley                             | 522     |
| Berwick                              | 209     |
| Bideford                             | 540     |
| Black Tar                            | 498     |
| Blackpool                            | 445     |
| Blacktoft                            | 179     |
| Blyth                                | 204     |
| Bognor Regis                         | 73      |
| Bonawe                               | 371c    |
| Boscastle                            | 544     |
| Boston                               | 166     |
| Bouley Bay                           | 1606a   |
| Bournemouth                          | 37      |
| Bovisand Pier                        | 15a     |
| Bowling                              | 406     |
| Bradwell Waterside                   | 123     |
| Bramble Creek                        | 129a    |
| Braye                                | 1603    |
| Bridlington                          | 181     |
| Bridport (West Bay)                  | 29      |
| Brightlingsea                        | 126     |
| Brighton Marina                      | 82      |
| Broadford Bay                        | 341     |
| Broadstairs                          | 102a    |
| Brodick Bay                          | 408     |
| Brough                               | 176a    |
| Bruichladdich                        | 380     |
| Buckie                               | 248     |
| Bucklers Hard                        | 42      |
| Bull Sand Fort                       | 171a    |
| Bunessan                             | 361     |
| Bur Wick                             | 282a    |
| Burghead                             | 250     |
| Burnham-On-Crouch                    | 122     |
| Burnham-On-Sea                       | 528     |
| Burntisland                          | 230     |
| Burra Firth                          | 291     |
| Burra Voe (Yell Sound)               | 290     |
| Burray Ness                          | 271     |
| Burry Port                           | 505     |
| Bursledon                            | 63b     |
| Burton Stather                       | 177     |
| Caernarfon                           | 475     |
| Caister-On-Sea                       | 143     |
| Calf Sound                           | 469     |
| Calshot Castle                       | 61      |
| Campbeltown                          | 393     |
| Cape Cornwall                        | 547a    |
| Cardiff                              | 514     |
| Cargreen                             | 14b     |
| Carloway                             | 321a    |
| Carradale                            | 393a    |
| Carsaig Bay                          | 387     |
| Carsaig Bay (Mull)                   | 359     |
| Castle Bay                           | 314a    |
| Cemaes Bay                           | 477a    |
| Chatham (Lock Approaches)            | 109     |
| Chelsea Bridge                       | 113a    |
| Chesil Beach                         | 30      |
| Chesil Cove                          | 31      |
| Chichester Harbour (Entrance)        | 68      |
| Christchurch (Entrance)              | 38      |
| Christchurch (Quay)                  | 38a     |
| Christchurch (Tuckton)               | 38b     |
| Clacton-On-Sea                       | 128     |
| Cleavel Point                        | 36d     |
| Clevedon                             | 525     |
| Clovelly                             | 541     |
| Clydebank (Rothesay Dock) **Neap (3) | 406a    |
| Connel                               | 371a    |
| Conwy                                | 471a    |
| Coquet Island                        | 205     |
| Corpach                              | 368     |
| Corran                               | 367     |
| Coryton                              | 110a    |
| Cotehele Quay                        | 14c     |
| Coulport                             | 399b    |
| Coverack                             | 4       |
| Cowes                                | 60      |
| Craighouse                           | 383     |
| Craignure                            | 365a    |
| Criccieth                            | 483a    |
| Cromarty                             | 258     |
| Cromer                               | 154     |
| Cullivoe                             | 292     |
| Dale Roads                           | 495     |
| Darnett Ness                         | 108c    |
| Dartmouth                            | 23      |
| Deal                                 | 98      |
| Deer Sound                           | 272     |
| Dornie Bridge                        | 349a    |
| Douglas                              | 468     |
| Dover                                | 89      |
| Drummore                             | 419     |
| Drummore                             | 420     |
| Duddon Bar                           | 437     |
| Dunbar                               | 222     |
| Dundee                               | 236     |
| Dungeness                            | 87      |
| Dunstaffnage Bay                     | 371     |
| Dury Voe                             | 288     |
| East Loch Tarbert (Loch Fyne)        | 394     |
| East Loch Tarbert (Outer Hebrides)   | 310     |
| Eastbourne                           | 84      |
| Eastham                              | 453     |
| Egilsay                              | 273a    |
| English And Welsh Grounds            | 526     |
| Erith                                | 111b    |
| Esha Ness (Hamna Voe)                | 293a    |
| Exmouth (Approaches)                 | 26b     |
| Exmouth Dock                         | 27      |
| Eyemouth                             | 221     |
| Fair Isle                            | 285     |
| Falmouth                             | 5       |
| Faslane                              | 402b    |
| Felixstowe Pier                      | 133a    |
| Ferryside                            | 504     |
| Fiddler's Ferry                      | 456a    |
| Fidra                                | 223     |
| Filey Bay                            | 182     |
| Fishguard                            | 490     |
| Flannan Isles                        | 323     |
| Flat Holm                            | 513a    |
| Fleetwood                            | 444     |
| Flixborough Wharf                    | 177a    |
| Folkestone                           | 88      |
| Folly Inn                            | 60a     |
| Foreland (Lifeboat Slip)             | 53a     |
| Formby                               | 448     |
| Fort Belan                           | 475a    |
| Foula                                | 296a    |
| Fowey                                | 8       |
| Fraserburgh                          | 246     |
| Fremington                           | 538     |
| Freshwater Bay                       | 48      |
| Gairloch                             | 337     |
| Galmisdale Pier                      | 354a    |
| Garelochhead                         | 402c    |
| Garlieston                           | 422     |
| Garston                              | 452a    |
| Gills Bay                            | 297a    |
| Girvan                               | 414     |
| Glasgow                              | 407     |
| Glenelg Bay                          | 351     |
| Glengarrisdale Bay                   | 375     |
| Golspie                              | 264     |
| Goole                                | 180     |
| Gott Bay                             | 357     |
| Grangemouth                          | 228     |
| Granton                              | 226     |
| Gravesend                            | 111a    |
| Great Yarmouth (Britannia Pier)      | 142a    |
| Great Yarmouth (Gorleston-On-Sea)    | 142     |
| Greenock                             | 404     |
| Greenway Quay                        | 23a     |
| Grimsby                              | 172     |
| Grovehurst Jetty                     | 106     |
| Halfway Shoal                        | 439c    |
| Hammersmith Bridge                   | 115     |
| Hartlepool                           | 188     |
| Harwich                              | 131     |
| Hastings                             | 85      |
| Haws Point                           | 439b    |
| Helensburgh                          | 403     |
| Helford River (Entrance)             | 4a      |
| Helmsdale                            | 265     |
| Herne Bay                            | 104     |
| Hestan Island                        | 424     |
| Heysham                              | 441     |
| Hilbre Island                        | 461     |
| Hillswick                            | 294     |
| Hinkley Point                        | 530     |
| Hirta (Bagh A' Bhaile)               | 322     |
| Holliwell Point                      | 121a    |
| Holy Island                          | 208     |
| Holyhead                             | 478     |
| Hull (Albert Dock)                   | 175     |
| Hull (Alexandra Dock)                | 174a    |
| Hull (King George Dock)              | 174     |
| Hullbridge                           | 122b    |
| Humber Bridge                        | 176     |
| Humber Sea Terminal                  | 172a    |
| Hunstanton                           | 161     |
| Hurst Point                          | 39      |
| Iken Cliffs                          | 136c    |
| Ilfracombe                           | 535     |
| Immingham                            | 173     |
| Inner Dowsing Light                  | 168     |
| Inveraray                            | 395     |
| Invergordon                          | 259     |
| Inverie Bay                          | 353     |
| Inverness                            | 256     |
| Inward Rocks                         | 519     |
| Iona                                 | 360     |
| Ipswich                              | 133     |
| Irvine                               | 411     |
| Isle Of Whithorn                     | 421     |
| Itchenor                             | 68c     |
| Jupiter Point                        | 14e     |
| Kettletoft Pier                      | 275     |
| Kew Bridge                           | 115a    |
| Kincardine                           | 229     |
| King's Lynn                          | 162     |
| Kirkcaldy                            | 231     |
| Kirkcudbright Bay                    | 422a    |
| Kirkwall                             | 273     |
| Kyle Of Durness                      | 301     |
| Kyle Of Lochalsh                     | 349     |
| Langstone Harbour                    | 66      |
| Lee-On-The-Solent                    | 64      |
| Leith                                | 225     |
| Lerwick                              | 287     |
| Les Ecrehou                          | 1607    |
| Les Minquiers                        | 1608    |
| Leverburgh                           | 310a    |
| Little Bernera                       | 321     |
| Little Haven                         | 492b    |
| Littlehampton                        | 74      |
| Liverpool (Gladstone Dock)           | 451     |
| Lizard Point                         | 3       |
| Llanddwyn Island                     | 480     |
| Llandudno                            | 471     |
| Loch A' Bhraige                      | 340     |
| Loch Beag                            | 384     |
| Loch Bervie                          | 327     |
| Loch Boisdale                        | 313     |
| Loch Carnan                          | 311a    |
| Loch Creran Head                     | 370b    |
| Loch Dunvegan                        | 344     |
| Loch Harport                         | 345     |
| Loch Hourn                           | 352     |
| Loch Inver                           | 332     |
| Loch Laxford                         | 328     |
| Loch Maddy                           | 311     |
| Loch Melfort                         | 383a    |
| Loch Moidart                         | 355     |
| Loch Nedd                            | 330     |
| Loch Ranza                           | 393b    |
| Loch Scresort                        | 353b    |
| Loch Shell                           | 309     |
| Loch Skipport                        | 312     |
| Loch Snizort (Uig Bay)               | 343     |
| Lochgoilhead                         | 399c    |
| London Bridge (Tower Pier)           | 113     |
| Looe                                 | 11      |
| Lossiemouth                          | 249     |
| Loth                                 | 274     |
| Lowestoft                            | 141     |
| Lulworth Cove                        | 34      |
| Lundy                                | 542     |
| Lyme Regis                           | 28      |
| Lymington                            | 40      |
| Machrihanish                         | 390     |
| Mallaig                              | 353a    |
| Margate                              | 103     |
| Martin's Haven                       | 493     |
| Maryport                             | 433     |
| Maseline Pier                        | 1603a   |
| Meikle Ferry                         | 262     |
| Mellon Charles                       | 336     |
| Menai Bridge                         | 473     |
| Methil                               | 232     |
| Mevagissey                           | 7       |
| Mid Yell                             | 290a    |
| Middlesbrough (Dock Entrance)        | 186     |
| Milford Haven                        | 496     |
| Millport                             | 398     |
| Minehead                             | 532     |
| Minsmere Sluice                      | 139a    |
| Mistley                              | 132     |
| Moelfre                              | 476a    |
| Montrose                             | 242     |
| Morecambe                            | 440b    |
| Mostyn Docks                         | 464     |
| Muckle Skerry                        | 270     |
| Mumbles                              | 508     |
| Mupe Bay                             | 34a     |
| Nab Tower                            | 70      |
| Nairn                                | 253     |
| Narlwood Rocks                       | 520     |
| Nato Jetty                           | 336a    |
| New Hythe                            | 109d    |
| New Quay                             | 488     |
| Newburgh                             | 236a    |
| Newcastle-Upon-Tyne                  | 203     |
| Newhaven                             | 83      |
| Newport                              | 515     |
| Newquay                              | 546     |
| Neyland                              | 497     |
| North Fambridge                      | 122a    |
| North Sunderland (Northumberland)    | 207     |
| North Woolwich                       | 112     |
| Northney                             | 68a     |
| Oban                                 | 372     |
| Orford Haven Bar                     | 136     |
| Orford Ness                          | 137     |
| Orford Quay                          | 136a    |
| Orsay                                | 379     |
| Osea Island                          | 123a    |
| Out Skerries                         | 289     |
| Outer Westmark Knock                 | 163     |
| Padstow                              | 545     |
| Pagham                               | 72      |
| Par                                  | 7a      |
| Peel                                 | 466     |
| Penzance (Newlyn)                    | 2       |
| Perranporth                          | 546a    |
| Perth                                | 236b    |
| Peterhead                            | 245     |
| Pierowall                            | 277     |
| Plockton                             | 339     |
| Plymouth (Devonport)                 | 14      |
| Poole (Entrance)                     | 36      |
| Poole Harbour                        | 36a     |
| Porlock Bay                          | 533     |
| Port Appin                           | 370     |
| Port Askaig                          | 382     |
| Port Cardigan                        | 489     |
| Port Dinorwic                        | 474     |
| Port Ellen                           | 381     |
| Port Erin                            | 469a    |
| Port Glasgow                         | 405     |
| Port Isaac                           | 544a    |
| Port St. Mary                        | 468a    |
| Port Talbot                          | 510     |
| Port William                         | 420a    |
| Port of Bristol (Avonmouth)          | 523     |
| Porth Dinllaen                       | 481     |
| Porth Trecastell                     | 479a    |
| Porth Ysgaden                        | 481a    |
| Porthcawl                            | 512     |
| Porthgain                            | 491     |
| Porthleven                           | 2a      |
| Portland                             | 33      |
| Portmahomack                         | 261     |
| Portnancon                           | 300     |
| Portpatrick                          | 415     |
| Portree                              | 342     |
| Portsmouth                           | 65      |
| Portsmouth (High Water Stand)        | 65a     |
| Pottery Pier                         | 36b     |
| Preston                              | 446     |
| Pwllheli                             | 483     |
| Ramsey                               | 467     |
| Ramsey Sound                         | 492     |
| Ramsgate                             | 102     |
| Rapness                              | 276     |
| Redbridge                            | 63      |
| Rhu Marina                           | 402a    |
| Richborough                          | 99      |
| Richmond Lock                        | 116     |
| River Tay Bar                        | 235     |
| River Tees Entrance                  | 185     |
| River Tyne (North Shields)           | 202     |
| River Yealm Entrance                 | 17      |
| Roa Island                           | 439a    |
| Rochester (Strood Pier)              | 109b    |
| Rockall                              | 324     |
| Rona                                 | 304     |
| Rosneath                             | 402     |
| Rosyth                               | 227     |
| Rothesay Bay                         | 399     |
| Rubh' A' Mhail                       | 377     |
| Rubha A' Bhodaich                    | 396     |
| Rubha Na Creige                      | 371d    |
| Ryde                                 | 58      |
| S.E. Long Sand                       | 117     |
| Salcombe                             | 20      |
| Salen                                | 363     |
| Salen  Sound Of Mull                 | 364a    |
| Saltash                              | 14a     |
| Sandown                              | 53      |
| Scalasaig                            | 374     |
| Scalloway                            | 295     |
| Scarborough                          | 183     |
| Scolpaig                             | 318a    |
| Scrabster                            | 298     |
| Sea Mills                            | 523b    |
| Seacombe (Alfred Dock)               | 452     |
| Seaham                               | 189     |
| Seil Sound                           | 373     |
| Selsey Bill                          | 69      |
| Sharpness Dock                       | 522a    |
| Sheerness                            | 108     |
| Shieldaig                            | 338     |
| Shillay                              | 317     |
| Shirehampton                         | 523a    |
| Shivering Sand                       | 116a    |
| Shoreham                             | 81      |
| Silloth                              | 432     |
| Skegness                             | 167     |
| Skomer Island                        | 494     |
| Slaughden Quay                       | 136b    |
| Solva                                | 492a    |
| Sound Of Gigha                       | 389     |
| Sound of Ulva                        | 362     |
| Southampton                          | 62      |
| Southend  Kintyre                    | 391     |
| Southend-On-Sea                      | 110     |
| Southwold                            | 140     |
| Sovereign Harbour                    | 84a     |
| Spurn Head                           | 171     |
| St Catherine Bay                     | 1606    |
| St Germans                           | 14f     |
| St Helier                            | 1605    |
| St Ives                              | 547     |
| St Peter Port                        | 1604    |
| St Thomas's Head                     | 525a    |
| St Tudwal's Roads                    | 482b    |
| St. Mary's                           | 1       |
| St. Mary's (Scapa Flow)              | 281     |
| Stackpole Quay                       | 501     |
| Stansore Point                       | 43      |
| Starcross                            | 27a     |
| Start Point                          | 21      |
| Steep Holm                           | 513b    |
| Stirling                             | 229b    |
| Stoke Gabriel (Duncannon)            | 23b     |
| Stonehaven                           | 243     |
| Stornoway                            | 308     |
| Stranraer                            | 414a    |
| Stroma                               | 297     |
| Stromness                            | 280     |
| Sudbrook                             | 517     |
| Sule Skerry                          | 299     |
| Sullom Voe                           | 293     |
| Sumburgh (Grutness Voe)              | 285a    |
| Sunderland                           | 190     |
| Sunk Dredged Channel                 | 171b    |
| Sunk Head                            | 130     |
| Swanage                              | 35      |
| Swansea                              | 509     |
| Tabs Head                            | 165     |
| Tanera Mor                           | 333     |
| Tarn Point                           | 436     |
| Tees (Newport) Bridge                | 187     |
| Teignmouth (Approaches)              | 26      |
| Teignmouth (New Quay)                | 26a     |
| Tenby                                | 502     |
| Tighnabruaich                        | 396a    |
| Tilbury                              | 111     |
| Tingwall                             | 279     |
| Tobermory                            | 364     |
| Toft Pier                            | 289a    |
| Torquay                              | 25      |
| Totland Bay                          | 46      |
| Totnes                               | 23c     |
| Trearddur Bay                        | 479     |
| Trefor                               | 480a    |
| Troon                                | 412     |
| Trwyn Dinmor                         | 476     |
| Turnchapel                           | 15      |
| Ullapool                             | 334     |
| Upnor                                | 109a    |
| Ventnor                              | 51      |
| Wadebridge                           | 545a    |
| Walton-On-The-Naze                   | 129     |
| Wareham (River Frome)                | 36c     |
| Warsash                              | 63a     |
| Watchet                              | 531     |
| Wellhouse Rock                       | 522b    |
| Wells                                | 157a    |
| Wemyss Bay                           | 399a    |
| West Burra Firth                     | 294a    |
| West Loch Tarbert                    | 320     |
| West Mersea                          | 124     |
| West Stones                          | 161a    |
| Weston-Super-Mare                    | 527     |
| Whitaker Beacon                      | 121     |
| Whitby                               | 184     |
| White House                          | 521     |
| Whitehall                            | 273b    |
| Whitehaven                           | 435     |
| Whitehills                           | 247a    |
| Whiteness Head                       | 254     |
| Whitsand Bay                         | 12      |
| Whitstable Approaches                | 105     |
| Wick                                 | 267     |
| Widewall Bay                         | 282     |
| Widnes                               | 456     |
| Winterton-On-Sea                     | 144     |
| Wisbech Cut                          | 164     |
| Woodbridge                           | 134a    |
| Woodbridge Haven                     | 134     |
| Workington                           | 434     |
| Worthing                             | 75      |
| Wouldham                             | 109c    |
| Yarmouth                             | 45      |
| Yelland Marsh                        | 537     |
