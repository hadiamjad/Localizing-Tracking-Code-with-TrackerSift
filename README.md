# Localizing-Tracking-Code-with-TrackerSift
Websites that deploy tracking scripts to profile user behavior and show targeted advertisements are unfortunately prevalent on the web. To protect privacy, users enable content-blockers, such as Disconnect, that use pre-defined rules (i.e., blocklists) to block do- mains that serve such tracking scripts. In response, trackers use advanced code refactoring techniques such as inlining and code bundling to merge tracking code with the core functionality. Block- ing such bundled code will cause significant breakage of the web page, hence cornering the users into disabling content-blockers. Therefore, trackers can easily circumvent existing content blockers, making them ineffective at protecting user privacy.
In this paper, we demonstrate, TrackerSift, a localization tool that performs a hierarchical search on web application entities (domain, hostname, script, and method) to precisely isolate the code responsible for tracking behavior. We take inspiration from traditional spectra-based fault localization and re-purpose it to find a code’s participation in tracking and functional behavior, which helps identify tracking code. We realize this tool in an online browser extension that localizes tracker-inducing code at page load time and removes all such code, disabling trackers without any breakage. TrackerSift outperforms other content blockers in that it finds the source of the tracker instead of symptoms making it more resilient against trackers. Our measurements on 100K web pages show that TrackerSift can accurately classify up to 94% code entities (i.e., script or method) as purely tracking-inducing or purely functional. Subsequently, it can potentially remove up to 98% tracking behavior by removing the tracking code. The demo video is available at https://youtu.be/xlSKszM81uI.

P.S This paper is submitted to ICSE 2022 Demonstrations Track.

### Implementation 
![image](https://user-images.githubusercontent.com/46374292/144059568-70722d40-ae94-470f-a2a0-fe23784b1b8e.png)


TrackerSift is the first tool that blocks the advertisement and tracking request at method level using this sequence oif events:
![image](https://user-images.githubusercontent.com/46374292/144059865-321046c2-7439-4c52-8228-6ee006dddf84.png)


## Files Distribution
### Python Server
It contains basic flask server to do some analysis

### All rest of the Files
These files are for chrome extension. 
![image](https://user-images.githubusercontent.com/46374292/144060381-8360e60e-7d43-44c1-8cae-4049fff42fa8.png)

> All rights reserved.
