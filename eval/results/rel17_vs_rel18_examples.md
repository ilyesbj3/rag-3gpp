# Rel-18 vs Rel-17 answers (config `best`)

*preliminary — gold set pending human validation.* Questions where the two answers cite different sections or where one release refused.

## s23-03 — What functionality does the UPF support?

**Rel-18** (§4.2.10, §5.8.2.6.3, §6.2.3):

> The User plane function (UPF) includes the following functionality (some or all may be supported in a single instance of a UPF):
> 
> - Anchor point for Intra-/Inter-RAT mobility (when applicable) [TS 23.501 §6.2.3].
> - Allocation of UE IP address/prefix (if supported) in response to SMF request [TS 23.501 §6.2.3].
> - External PDU Session point of interconnect to Data Network [TS 23.501 §6.2.3].
> - Packet routing & forwarding (e.g. support of Uplink classifier to route traffic flows to an instance of a data network, support of Branching point to support multi-homed PDU Session, support of traffic forwarding within a 5G VN group (UPF local switching, via N6, via N19)) [TS 23.501 §6.2.3].
> - Packet inspection (e.g. Application detection based on service data flow template and the optional PFDs received from the SMF in addition) [TS 23.501 §6.2.3].
> - User Plane part of policy rule enforcement, e.g. Gating, Redirection, Traffic steering [TS 23.501 §6.2.3].
> - Lawful intercept (UP collection) [TS 23.501 §6.2.3].
> - Traffic usage reporting [TS 23.501 §6.2.3], including reporting of usage information to the SMF based on different triggers such as periodic reporting, usage thresholds, and report on demand [TS 23.501 §5.8.2.6.3].
> - QoS handling for user plane, e.g. UL/DL rate enforcement, Reflective QoS marking in DL [TS 23.501 §6.2.3].
> - Uplink Traffic verification (SDF to QoS Flow mapping) [TS 23.501 §6.2.3].
> - Transport level packet marking in the uplink and downlink [TS 23.501 §6.2.3].
> - Downlink packet buffering and downlink data notification triggering [TS 23.501 §6.2.3].
> - Sending and forwarding of one or more "end marker" to the source NG-RAN node [TS 23.501 §6.2.3].
> - Functionality to respond to Address Resolution Protocol (ARP) requests and / or IPv6 Neighbour Solicitation requests based on local cache information for the Ethernet PDUs, by providing the MAC address corresponding to the IP address sent in the request [TS 23.501 §6.2.3].
> - Packet duplication in downlink direction and elimination in uplink direction in GTP-U layer [TS 23.501 §6.2.3].
> - NW-TT functionality [TS 23.501 §6.2.3].
> - High latency communication, see clause 5.31.8 of TS 23.501 [TS 23.501 §6.2.3].
> - ATSSS Steering functionality to steer the MA PDU Session traffic, refer to clause 5.32.6 of TS 23.501 [TS 23.501 §6.2.3].
> - Inter PLMN UP Security (IPUPS) functionality, specified in clause 5.8.2.14 of TS 23.501 [TS 23.501 §6.2.3].
> - Event exposure, including exposure of network information (QoS monitoring information as specified in clause 5.8.2.18 of TS 23.501, events as specified in clause 5.2.26.2 of TS 23.502), exposure of data collected for analytics (as specified in clause 5.2.26.2 of TS 23.502), and exposure of the TSC management information as specified in clause 5.8.5.14 of TS 23.501 [TS 23.501 §6.2.3].
> - Exposure of the UE information (e.g. UE IP address translation information as specified in clause 5.2.26.3 and clause 4.15.10 of TS 23.502 if Network address translation functionality of the UE IP address is deployed within UPF) [TS 23.501 §6.2.3].
> - Support PDU Set based handling as defined in clause 5.37.5 of TS 23.501 [TS 23.501 §6.2.3].
> - Optionally, MPTCP Proxy functionality communicating with the MPTCP functionality in the UE by using the MPTCP protocol, as defined in clause 5.32.6.2.1 [TS 23.501 §4.2.10].
> - Optionally, MPQUIC Proxy functionality communicating with the MPQUIC functionality in the UE by using the QUIC protocol and its multipath extensions, as defined in clause 5.32.6.2.2 [TS 23.501 §4.2.10].
> - Optionally, ATSSS-LL functionality (there is no user plane protocol defined between the ATSSS-LL functionality in the UE and the ATSSS-LL functionality in the UPF) [TS 23.501 §4.2.10].
> - Performance Measurement Functionality (PMF), which may be used by the UE to obtain access performance measurements over the user-plane of 3GPP access and/or non-3GPP access [TS 23.501 §4.2.10].

**Rel-17** (§4.2.10, §5.12.1, §5.8.2.6.3, §6.2.3):

> The User plane function (UPF) includes the following functionality (some or all of which may be supported in a single instance of a UPF):
> 
> - Anchor point for Intra-/Inter-RAT mobility (when applicable) [TS 23.501 §6.2.3].
> - Allocation of UE IP address/prefix (if supported) in response to SMF request [TS 23.501 §6.2.3].
> - External PDU Session point of interconnect to Data Network [TS 23.501 §6.2.3].
> - Packet routing & forwarding (e.g. support of Uplink classifier to route traffic flows to an instance of a data network, support of Branching point to support multi-homed PDU Session, support of traffic forwarding within a 5G VN group (UPF local switching, via N6, via N19)) [TS 23.501 §6.2.3].
> - Packet inspection (e.g. Application detection based on service data flow template and the optional PFDs received from the SMF in addition) [TS 23.501 §6.2.3].
> - User Plane part of policy rule enforcement, e.g. Gating, Redirection, Traffic steering) [TS 23.501 §6.2.3].
> - Lawful intercept (UP collection) [TS 23.501 §6.2.3].
> - Traffic usage reporting [TS 23.501 §6.2.3], and collection and reporting of usage data to SMF [TS 23.501 §5.12.1][TS 23.501 §5.8.2.6.3].
> - QoS handling for user plane, e.g. UL/DL rate enforcement, Reflective QoS marking in DL [TS 23.501 §6.2.3].
> - Uplink Traffic verification (SDF to QoS Flow mapping) [TS 23.501 §6.2.3].
> - Transport level packet marking in the uplink and downlink [TS 23.501 §6.2.3].
> - Downlink packet buffering and downlink data notification triggering [TS 23.501 §6.2.3].
> - Sending and forwarding of one or more "end marker" to the source NG-RAN node [TS 23.501 §6.2.3].
> - Functionality to respond to Address Resolution Protocol (ARP) requests and / or IPv6 Neighbour Solicitation requests based on local cache information for the Ethernet PDUs (providing the MAC address corresponding to the IP address sent in the request) [TS 23.501 §6.2.3].
> - Packet duplication in downlink direction and elimination in uplink direction in GTP-U layer [TS 23.501 §6.2.3].
> - NW-TT functionality [TS 23.501 §6.2.3].
> - High latency communication [TS 23.501 §6.2.3].
> - ATSSS Steering functionality to steer the MA PDU Session traffic [TS 23.501 §6.2.3].
> - Inter PLMN UP Security (IPUPS) functionality [TS 23.501 §6.2.3].
> - Exposure of network information, i.e. the QoS monitoring information [TS 23.501 §6.2.3].
> - MPTCP Proxy functionality (may support) [TS 23.501 §4.2.10].
> - ATSSS-LL functionality (may support) [TS 23.501 §4.2.10].
> - Performance Measurement Functionality (PMF) (may support) [TS 23.501 §4.2.10].

## s23-10 — How does the AMF allocate a registration area to a UE over 3GPP access?

**Rel-18** (§5.3.2.3):

> When a UE registers with the network over the 3GPP access, the AMF allocates a set of tracking areas in TAI List to the UE [TS 23.501 §5.3.2.3]. 
> 
> When allocating the registration area (the set of tracking areas in TAI List) to the UE, the AMF may take into account various information such as Mobility Pattern and Allowed/Non-Allowed Area [TS 23.501 §5.3.2.3]. 
> 
> Additionally, the following specific allocation rules apply:
> * An AMF which has the whole PLMN as serving area may alternatively allocate the whole PLMN ("all PLMN") as a registration area to a UE in MICO mode [TS 23.501 §5.3.2.3].
> * When allocating a registration area for a UE registered for Disaster Roaming service, the AMF shall only consider TAIs covering the area with the Disaster Condition [TS 23.501 §5.3.2.3].
> * The 5G System supports allocating a Registration Area using a single TAI List which includes tracking areas of any NG-RAN nodes in the Registration Area for a UE [TS 23.501 §5.3.2.3].
> * In the case of SNPN, the TAI list allocated by the AMF does not support Tracking Areas belonging to different SNPNs [TS 23.501 §5.3.2.3].
> * When generating the TAI list, the AMF shall include only TAIs that are applicable on the 3GPP access type [TS 23.501 §5.3.2.3].

**Rel-17** (§5.3.2.3, §5.4.1.3):

> When a UE registers with the network over the 3GPP access, the AMF allocates a set of tracking areas in TAI List to the UE [TS 23.501 §5.3.2.3]. 
> 
> When the AMF allocates the registration area (the set of tracking areas in TAI List) to the UE, it may take into account various information such as Mobility Pattern and Allowed/Non-Allowed Area [TS 23.501 §5.3.2.3]. 
> 
> Additionally:
> - An AMF which has the whole PLMN as serving area may alternatively allocate the whole PLMN ("all PLMN") as a registration area to a UE in MICO mode [TS 23.501 §5.3.2.3].
> - When the AMF allocates a registration area for a UE registered for Disaster Roaming service, the AMF shall only consider TAIs covering the area with the Disaster Condition [TS 23.501 §5.3.2.3].
> - When the AMF indicates MICO mode to a UE, the registration area is not constrained by paging area size [TS 23.501 §5.4.1.3].

## s24-04 — When is timer T3510 started and stopped, and what happens when it expires?

**Rel-18** (§5.4.1.2.4.5, §5.4.1.3.7, §5.5.1.2.7, §5.5.1.3.7):

> Based on the provided documents, timer T3510 is started, stopped, and handled upon expiration as follows:
> 
> * **When it is started:**
>  * Timer T3510 is started upon the transmission of a REGISTRATION REQUEST message.
>  * If timer T3510 was running and stopped when the UE received an AUTHENTICATION REQUEST message and detected an authentication failure (and the associated procedures have not yet been completed), or when the network fails the authentication check, the UE shall start any retransmission timers including T3510 [TS 24.501 §5.4.1.3.7][TS 24.501 §5.4.1.2.4.5].
> 
> * **When it is stopped:**
>  * Timer T3510 is stopped when a REGISTRATION ACCEPT message or a REGISTRATION REJECT message is received.
>  * Timer T3510 shall be stopped if still running during abnormal cases in the UE during initial registration or mobility and periodic registration update (such as cases c, d, and e) [TS 24.501 §5.5.1.2.7][TS 24.501 §5.5.1.3.7].
> 
> * **What happens when it expires:**
>  * If T3510 expired during the registration procedure for initial registration, the UE shall start T3511 or T3502 as specified in clause 5.5.1.2.7 [TS 24.501 §5.5.1.2.7].
>  * If T3510 expired during the registration procedure for mobility and periodic registration update, the UE shall start T3511 or T3502 as specified in clause 5.5.1.3.7 [TS 24.501 §5.5.1.3.7].

**Rel-17** (§10.2):

> Timer T3510 is started, stopped, and handled upon expiry as follows:
> 
> - **Start of T3510:**
>  - T3510 is started upon the transmission of the REGISTRATION REQUEST message [TS 24.501 §10.2].
> 
> - **Stop of T3510:**
>  - T3510 is stopped normally when a REGISTRATION ACCEPT message is received or a REGISTRATION REJECT message is received [TS 24.501 §10.2].
> 
> - **Expiry of T3510:**
>  - If T3510 expires during the registration procedure for initial registration, start T3511 or T3502 as specified in subclause 5.5.1.2.7 [TS 24.501 §10.2].
>  - If T3510 expires during the registration procedure for mobility and periodic registration update, start T3511 or T3502 as specified in subclause 5.5.1.3.7 [TS 24.501 §10.2].

## s24-05 — What is the default value of timer T3502 and when is it started?

**Rel-18** (§10.2, §5.3.8, §5.5.1.2.7, §5.5.1.3.7):

> The default value of timer T3502 is 12 minutes [TS 24.501 §5.3.8][TS 24.501 §10.2]. 
> 
> Timer T3502 is started when the registration attempt counter is equal to 5 and the value of the timer as indicated by the network is not zero [TS 24.501 §5.5.1.3.7][TS 24.501 §5.5.1.2.7][TS 24.501 §10.2].

**Rel-17** (§10.2):

> The default value of timer T3502 is 12 minutes [TS 24.501 §10.2]. 
> 
> Timer T3502 is started at registration failure and the attempt counter is equal to 5 [TS 24.501 §10.2].

## s24-09 — What does the UE do when it accepts a SECURITY MODE COMMAND message?

**Rel-18** (§5.4.2.3):

> When the UE accepts a SECURITY MODE COMMAND message, it performs the following actions:
> 
> * Performs an integrity check of the message and checks that the received Replayed UE security capabilities IE has not been altered compared to the latest values sent to the network [TS 24.501 §5.4.2.3].
> * Handles any included EAP-success message and the ABBA as described in clauses 5.4.1.2.2.8, 5.4.1.2.3.1, 5.4.1.2.3A.1, 5.4.1.2.3B.1, and 5.4.1.2.3C.1 if the SECURITY MODE COMMAND message includes an EAP-success message [TS 24.501 §5.4.2.3].
> * If received under specific conditions (such as for emergency services or with specific device types like W-AGF acting on behalf of an FN-RG or N5GC device, or 5G-RG acting on behalf of an AUN3 device) with ngKSI value "000" and 5G-IA0 and 5G-EA0 as selected algorithms, locally derives and takes into use the 5G NAS security context, and deletes the existing current 5G NAS security context [TS 24.501 §5.4.2.3].
> * Accepts a SECURITY MODE COMMAND message indicating the "null integrity protection algorithm" 5G-IA0 only under the specific permitted conditions (e.g., emergency services or specified device types) [TS 24.501 §5.4.2.3].
> * Takes a non-current native 5G NAS security context into use (making it the current native context) and deletes the mapped 5G NAS security context, if the type of security context flag is set to "native security context" and the ngKSI matches a valid non-current native context while a mapped context is current [TS 24.501 §5.4.2.3].
> * Ignores the Replayed S1 UE security capabilities IE if it is included [TS 24.501 §5.4.2.3].
> * Takes the 5G NAS security context indicated in the message into use [TS 24.501 §5.4.2.3].
> * Resets the uplink NAS COUNT counter if the SECURITY MODE COMMAND message is received to take into use a context created after successful 5G AKA or EAP-AKA primary authentication, or if the message includes the type of security context flag set to "mapped security context" in the NAS key set identifier IE where the ngKSI does not match the current 5G NAS security context (if it is a mapped context) [TS 24.501 §5.4.2.3].
> * Sets the downlink NAS COUNT of the new 5G NAS security context to 0 if the message was successfully integrity checked using an estimated downlink NAS COUNT equal to 0; otherwise, sets it to the downlink NAS COUNT used for the successful integrity check, provided the message does not indicate the "null integrity protection algorithm" 5G-IA0 [TS 24.501 §5.4.2.3].
> * Derives a new K'AMF (as specified in 3GPP TS 33.501 [24]) and sets both uplink and downlink NAS COUNTs to zero if the message includes the horizontal derivation parameter indicating "KAMF derivation is required" [TS 24.501 §5.4.2.3].
> * Activates the new 5G NAS security context over the non-current access (setting downlink and uplink NAS COUNTs to zero or leaving them unchanged depending on whether a primary authentication procedure was completed) if registered with the same PLMN over both 3GPP and non-3GPP accesses and the UE is in 5GMM-IDLE mode over the non-current access [TS 24.501 §5.4.2.3].
> * Checks whether the SECURITY MODE COMMAND message indicates the ngKSI of the current 5GS security context (if it is a mapped 5G NAS security context) in order not to re-generate the K'AMF, when the message includes the type of security context flag set to "mapped security context" in the NAS key set identifier IE [TS 24.501 §5.4.2.3].
> * Sends a SECURITY MODE COMPLETE message, integrity protected with the selected 5GS integrity algorithm and 5G NAS integrity key, and ciphered with the selected 5GS ciphering algorithm and 5G NAS ciphering key based on the KAMF or mapped K'AMF indicated by the ngKSI [TS 24.501 §5.4.2.3].
> * Sets the security header type of the SECURITY MODE COMPLETE message to "integrity protected and ciphered with new 5G NAS security context" [TS 24.501 §5.4.2.3].
> * From that time onward, ciphers and integrity protects all NAS signalling messages with the selected 5GS integrity and ciphering algorithms [TS 24.501 §5.4.2.3].
> * Includes its IMEISV, EUI-64, or MAC address/MAC address usage restriction indication in the appropriate IE of the SECURITY MODE COMPLETE message if requested by the AMF or required by device/access type rules [TS 24.501 §5.4.2.3].
> * Includes the entire unciphered initial NAS message (REGISTRATION REQUEST, DEREGISTRATION REQUEST, SERVICE REQUEST, or CONTROL PLANE SERVICE REQUEST) in the NAS message container IE of the SECURITY MODE COMPLETE message if the SECURITY MODE COMMAND includes the Additional 5G security information IE with the RINMR bit set to "Retransmission of the initial NAS message requested" or if the UE sent a REGISTRATION REQUEST message without a valid 5G NAS security context prior to receiving the SECURITY MODE COMMAND message [TS 24.501 §5.4.2.3].
> * Uses the Selected EPS NAS security algorithms IE according to 3GPP TS 33.501 [24] if operating in single-registration mode, including setting the value of the Selected EPS NAS security algorithms IE in the 5G NAS security context to the NAS security algorithms received from the source MME after an inter-system change from S1 mode to N1 mode in 5GMM-CONNECTED mode in a network supporting the N26 interface [TS 24.501 §5.4.2.3].

**Rel-17** (§5.4.2.3, §8.2.26.2):

> When the UE accepts a SECURITY MODE COMMAND message, it performs the following actions:
> 
> * It checks whether the security mode command can be accepted by performing an integrity check of the message and checking that the received Replayed UE security capabilities IE has not been altered compared to the latest values that the UE sent to the network [TS 24.501 §5.4.2.3].
> * If the message includes an EAP-success message, the UE handles the EAP-success message and the ABBA as described in subclauses 5.4.1.2.2.8, 5.4.1.2.3.1, 5.4.1.2.3A.1, and 5.4.1.2.3B.1 [TS 24.501 §5.4.2.3].
> * If the message is received with ngKSI value "000" and 5G-IA0 and 5G-EA0 as selected 5G NAS security algorithms under specific conditions (e.g., related to emergency services, W-AGF acting on behalf of FN-RG or N5GC device), the UE locally derives and takes into use the 5G NAS security context and deletes the existing current 5G NAS security context [TS 24.501 §5.4.2.3].
> * The UE accepts a SECURITY MODE COMMAND message indicating the "null integrity protection algorithm" 5G-IA0 only under the specific conditions defined for emergency services, W-AGF acting on behalf of an FN-RG, or W-AGF acting on behalf of an N5GC device [TS 24.501 §5.4.2.3].
> * If the type of security context flag is set to "native security context" and the ngKSI matches a valid non-current native 5G NAS security context while the UE has a mapped 5G NAS security context as current, the UE takes the non-current native 5G NAS security context into use (making it current) and deletes the mapped 5G NAS security context [TS 24.501 §5.4.2.3].
> * The UE ignores the Replayed S1 UE security capabilities IE if it is included [TS 24.501 §5.4.2.3].
> * The UE takes the 5G NAS security context indicated in the message into use [TS 24.501 §5.4.2.3].
> * The UE resets the uplink NAS COUNT counter if:
>  * a) the message is received to take into use a 5G NAS security context created after successful execution of 5G AKA or EAP based primary authentication and key agreement; or
>  * b) the message includes the type of security context flag set to "mapped security context" in the NAS key set identifier IE and the ngKSI does not match the current 5G NAS security context, if it is a mapped 5G NAS security context [TS 24.501 §5.4.2.3].
> * If a new 5G NAS security context is taken into use without the "null integrity protection algorithm" 5G-IA0, the UE sets the downlink NAS COUNT either to 0 (if integrity checked using an estimated downlink NAS COUNT equal to 0) or to the downlink NAS COUNT used for successful integrity checking of the SECURITY MODE COMMAND message [TS 24.501 §5.4.2.3].
> * If the message includes the horizontal derivation parameter indicating "KAMF derivation is required", the UE derives a new K'AMF and sets both uplink and downlink NAS COUNTs to zero [TS 24.501 §5.4.2.3]. Additionally, for the non-current access when registered over both 3GPP and non-3GPP accesses:
>  * If in 5GMM-IDLE mode over the non-current access, the UE activates the new 5G NAS security context and sets downlink and uplink NAS COUNTs to zero [TS 24.501 §5.4.2.3].
>  * If in 5GMM-CONNECTED mode over the non-current access, the AMF sends the SECURITY MODE COMMAND over that access [TS 24.501 §5.4.2.3].
> * If the message includes the horizontal derivation parameter indicating "KAMF derivation is not required" or lacks the Additional 5G security information IE, and the UE is registered over both 3GPP and non-3GPP accesses:
>  * If in 5GMM-IDLE mode over the non-current access, the UE activates the new 5G NAS security context (setting NAS COUNTs to zero if a primary authentication and key agreement procedure was completed before the security mode control procedure; otherwise, leaving them unchanged) [TS 24.501 §5.4.2.3].
>  * If in 5GMM-CONNECTED mode over the non-current access, the AMF sends the SECURITY MODE COMMAND over the non-current access [TS 24.501 §5.4.2.3].
> * The UE sends a SECURITY MODE COMPLETE message integrity protected and ciphered with the selected 5GS integrity and ciphering algorithms and keys based on the KAMF or mapped K'AMF [TS 24.501 §5.4.2.3]. The security header type is set to "integrity protected and ciphered with new 5G NAS security context" [TS 24.501 §5.4.2.3].
> * From that time onward, the UE ciphers and integrity protects all NAS signalling messages with the selected algorithms [TS 24.501 §5.4.2.3].
> * If requested by the AMF, the UE includes its IMEISV (if supporting at least one 3GPP access technology), its EUI-64 in the non-IMEISV PEI IE (if supporting no 3GPP access technology and supporting NAS over untrusted/trusted non-3GPP access), or the MAC address and MAC address usage restriction indication (if the 5G-RG contains neither an IMEISV nor an IMEI or when W-AGF acts on behalf of FN-RG or N5GC device) in the SECURITY MODE COMPLETE message [TS 24.501 §5.4.2.3][TS 24.501 §8.2.26.2].
> * If the SECURITY MODE COMMAND includes the Additional 5G security information IE with the RINMR bit set to "Retransmission of the initial NAS message requested" during an ongoing registration or service request procedure, or if the UE sent a REGISTRATION REQUEST without a valid 5G NAS security context prior to receiving the SECURITY MODE COMMAND, the UE includes the entire unciphered initial NAS message (REGISTRATION REQUEST, SERVICE REQUEST, or CONTROL PLANE SERVICE REQUEST) in the NAS message container IE of the SECURITY MODE COMPLETE message [TS 24.501 §5.4.2.3].
> * If operating in single-registration mode, the UE uses the Selected EPS NAS security algorithms IE according to 3GPP TS 33.501 [TS 24.501 §5.4.2.3].
> * For a UE operating in single-registration mode in a network supporting N26 after an inter-system change from S1 mode to N1 mode in 5GMM-CONNECTED mode, the UE sets the value of the Selected EPS NAS security algorithms IE in the 5G NAS security context to the NAS security algorithms received from the source MME in S1 mode [TS 24.501 §5.4.2.3].

## x-02 — How is a PDU session established, and which 5GSM messages are exchanged?

**Rel-18** (no citation):

> I could not find this information in the documents.

**Rel-17** (§4.2, §6.1.1, §6.2.3, §8.3.1.5, §8.3.2.2):

> To establish a PDU session, the UE executes the UE-requested PDU session establishment procedure [TS 24.501 §6.2.3]. 
> 
> The general procedure and characteristics of 5GS session management (5GSM) for PDU session handling are as follows:
> - The 5GSM procedures can be performed only if a 5GMM context has been established between the UE and the AMF, and the secure exchange of NAS messages has been initiated by the AMF [TS 24.501 §6.1.1].
> - Once the UE is successfully registered to a PLMN, a PDU session can be established [TS 24.501 §6.1.1].
> - A UE may establish multiple PDU sessions, to the same data network or to different data networks, via 3GPP and via non-3GPP access networks at the same time [TS 24.501 §6.2.3].
> - A 5GSM message is piggybacked in specific 5GS mobility management (5GMM) transport messages, allowing the UE, the AMF, and the SMF to execute the 5GMM procedure and the 5GSM procedure in parallel [TS 24.501 §4.2].
> - The session management messages between the UE and the SMF are transferred via the AMF [TS 24.501 §6.2.3].
> 
> Regarding specific 5GSM messages and information elements involved during establishment:
> - The 5GSM capability information element (IE) is included in the message when the UE requests to establish a new PDU session (or transfer an existing PDN connection) and any of the 5GSM capabilities supported by the UE are relevant for the PDU session [TS 24.501 §8.3.1.5].
> - The 5GSM cause information element is included when the selected PDU session type is different from the PDU session type requested by the UE [TS 24.501 §8.3.2.2].

## x-04 — What is the registration area and how does the periodic registration update timer work?

**Rel-18** (no citation):

> I could not find this information in the documents.

**Rel-17** (§5.16.4.4, §5.3.2.4, §5.31.7.5, §5.4.1.1):

> * **UE Registration Area:** The UE location is known by the network on a Tracking Area List granularity for UEs in CM-IDLE state [TS 23.501 §5.4.1.1]. A registration area that is not the "all PLMN" registration area may be allocated to a UE in MICO mode, and the UE determines if it is within the registration area or not when it has MO data or MO signalling.
> * **Periodic Registration Update Timer Operation:**
>  - Whenever a UE in RM-REGISTERED state enters CM-IDLE state, it starts a periodic registration timer according to the periodic registration timer value received from the AMF during a Registration procedure [TS 23.501 §5.4.1.1].
>  - The AMF allocates a periodic registration timer value to the UE based on local policies, subscription information, and information provided by the UE [TS 23.501 §5.4.1.1].
>  - After the expiry of the periodic registration timer, the UE shall perform a periodic registration [TS 23.501 §5.4.1.1]. If the UE moves out of network coverage when its periodic registration timer expires, the UE shall perform a Registration procedure when it next returns to the coverage [TS 23.501 §5.4.1.1].
>  - Over 3GPP access, an Emergency Registered UE when its Periodic Registration Update timer expires shall not initiate a Periodic Registration Update procedure but shall enter the RM-DEREGISTERED state [TS 23.501 §5.16.4.4].
>  - For a UE supporting 'Strictly Periodic Registration Timer Indication' that receives the indication from the AMF, the UE and AMF shall start the periodic registration timer after completion of the Registration procedure, and shall neither stop nor restart the timer when the UE enters CM-CONNECTED, keeping it running while in CM-CONNECTED state and after returning to CM-IDLE state [TS 23.501 §5.31.7.5]. If and only when this timer expires and the UE is in CM-IDLE, the UE shall perform a Periodic Registration Update [TS 23.501 §5.31.7.5]. If it expires while the UE is in CM-CONNECTED state, the AMF and the UE restart the timer while still applying 'Strictly Periodic Registration Timer Indication' [TS 23.501 §5.31.7.5].
>  - If the periodic registration timer is renegotiated during a Registration procedure, and if the periodic registration timer is running, then the periodic registration timer is stopped and restarted using the renegotiated value even when the Strictly Periodic Registration Timer Indication was provided to the UE [TS 23.501 §5.31.7.5].
>  - The AMF shall not provide a Periodic Registration Timer for the UE over a Non-3GPP access [TS 23.501 §5.3.2.4].

## x-05 — How are user plane resources of existing PDU sessions re-activated with the service request procedure?

**Rel-18** (§5.6.1.4.1):

> To re-activate user plane resources of existing PDU sessions using the service request procedure, the following principles and actions apply according to the documents:
> 
> * The UE includes the Uplink data status IE in the SERVICE REQUEST message [TS 24.501 §5.6.1.4.1].
> * If the UE is not in NB-N1 mode, or if the UE is in NB-N1 mode and does not indicate a request to have user-plane resources established for a number of PDU sessions that exceeds the UE's maximum number of supported user-plane resources, the AMF shall indicate the SMF to re-establish the user-plane resources for the corresponding PDU sessions [TS 24.501 §5.6.1.4.1].
> * The AMF includes the PDU session reactivation result IE in the SERVICE ACCEPT message to indicate the user-plane resources re-establishment result of the PDU sessions for which the UE requested to re-establish the user-plane resources [TS 24.501 §5.6.1.4.1].
> * For a PDU session for LADN, the AMF determines the UE presence in LADN service area and forwards the UE presence in LADN service area towards the SMF [TS 24.501 §5.6.1.4.1].
> * If the Allowed PDU session status IE is included in the SERVICE REQUEST message, the AMF notifies the SMF whether reactivation of user-plane resources for corresponding PDU session(s) associated with non-3GPP access can be performed or cannot be performed based on whether the corresponding PDU session IDs are indicated in the Allowed PDU session status IE (and whether supported user-plane resource limits are respected for UEs in NB-N1 mode) [TS 24.501 §5.6.1.4.1].
> * If user-plane resources are successfully reactivated for a PDU session indicated by the UE in the Allowed PDU session status IE as allowed to be re-established over 3GPP access, the UE considers the corresponding PDU session to be associated with the 3GPP access, and the AMF and SMF update the associated access type [TS 24.501 §5.6.1.4.1].
> * If user-plane resources cannot be established for a PDU session, the AMF includes the PDU session reactivation result IE in the SERVICE ACCEPT message indicating that they cannot be re-established, along with a PDU session reactivation result error cause IE with a specific 5GMM cause (e.g., #43 "LADN not available", #28 "restricted service area", #92 "insufficient user-plane resources for the PDU session", or #69 "insufficient resources for specific slice") depending on the reason provided by the SMF or determined by the AMF [TS 24.501 §5.6.1.4.1].

**Rel-17** (§5.6.1.1, §5.6.1.4.1, §5.6.1.4.2):

> To re-activate user-plane resources of existing PDU sessions using the service request procedure, the procedure changes the 5GMM mode from 5GMM-IDLE to 5GMM-CONNECTED mode, and is used to request the establishment of user-plane resources for PDU sessions that are established without user-plane resources (when the UE is not using 5GS services with control plane CIoT 5GS optimization) [TS 24.501 §5.6.1.1]. 
> 
> The handling and re-establishment of user-plane resources proceed according to the following rules:
> 
> * **Initiation and Checks:** 
>  - If the Uplink data status IE is included in the SERVICE REQUEST message and the UE is not in NB-N1 mode, or is in NB-N1 mode without requesting user-plane resources for a number of PDU sessions exceeding the UE's maximum supported number, the AMF shall indicate the SMF to re-establish the user-plane resources for the corresponding PDU sessions [TS 24.501 §5.6.1.4.1].
>  - For a UE using 5GS services with control plane CIoT 5GS optimization, the AMF shall indicate the SMF to re-establish the user-plane resources for the corresponding PDU sessions [TS 24.501 §5.6.1.4.2].
> 
> * **Successful Re-establishment:**
>  - The AMF includes the PDU session reactivation result IE in the SERVICE ACCEPT message to indicate the successfully re-established user-plane resources for the corresponding PDU sessions, if any [TS 24.501 §5.6.1.4.1][TS 24.501 §5.6.1.4.2].
>  - If the PDU session reactivation result IE in the SERVICE ACCEPT message indicates that user-plane resources have been successfully reactivated for a PDU session requested by the UE in the Allowed PDU session status IE, the UE considers the corresponding PDU session to be associated with the 3GPP access [TS 24.501 §5.6.1.4.1].
>  - When user-plane resources are successfully reactivated over the 3GPP access, the AMF and SMF update the associated access type of the corresponding PDU session [TS 24.501 §5.6.1.4.1].
> 
> * **Unsuccessful Re-establishment:**
>  - If user-plane resources cannot be established for a PDU session, the AMF includes the PDU session reactivation result IE in the SERVICE ACCEPT message indicating that user-plane resources for the corresponding PDU session cannot be re-established [TS 24.501 §5.6.1.4.1][TS 24.501 §5.6.1.4.2].
>  - If the PDU session reactivation result IE indicates that user-plane resources cannot be established for a PDU session requested in the Allowed PDU session status IE, the UE considers the corresponding PDU session to be associated with the non-3GPP access [TS 24.501 §5.6.1.4.1].
>  - The AMF shall include the PDU session reactivation result error cause IE with specific 5GMM causes under conditions such as:
>  - Cause #43 "LADN not available", if the UE is located out of the LADN service area [TS 24.501 §5.6.1.4.1][TS 24.501 §5.6.1.4.2].
>  - Cause #28 "restricted service area", if only prioritized services are allowed [TS 24.501 §5.6.1.4.1][TS 24.501 §5.6.1.4.2].
>  - Cause #92 "insufficient user-plane resources for the PDU session", if the resource is not available in the UPF, or if a UE in NB-N1 mode exceeds the limit of established user-plane resources [TS 24.501 §5.6.1.4.1][TS 24.501 §5.6.1.4.2].
>  - Cause #69 "insufficient resources for specific slice", if the S-NSSAI associated with the PDU session is unavailable due to NSAC [TS 24.501 §5.6.1.4.1].
>  - Otherwise, an optional error cause may be included to indicate the failure reason [TS 24.501 §5.6.1.4.1].

## x-06 — How does a UE deregister from the 5G System, from the registration management states to the NAS messages used?

**Rel-18** (§4.4.6, §5.5.2.2.1):

> To initiate the UE-initiated de-registration procedure, the UE shall enter the state 5GMM-DEREGISTERED-INITIATED [TS 24.501 §5.5.2.2.1]. 
> 
> ### UE-Initiated De-Registration Procedure and NAS Messages
> 
> 1. **Sending the DEREGISTRATION REQUEST message:**
>  - If the UE is to be switched off, it shall try for a period of 5 seconds to send the DEREGISTRATION REQUEST message and may be switched off as soon as it has been sent [TS 24.501 §5.5.2.2.1].
>  - If the network indicated support for the unavailability period in the last registration procedure, an event makes the UE unavailable for a certain period (not due to NR satellite access discontinuous coverage), and the UE is unable to store its 5GMM and 5GSM contexts, the UE shall include the unavailability period duration in the Unavailability information IE, set the Unavailability type to "unavailability due to UE reasons", and set the De-registration type to "Normal de-registration" in the DEREGISTRATION REQUEST message [TS 24.501 §5.5.2.2.1].
>  - If the UE is sending the DEREGISTRATION REQUEST message from 5GMM-IDLE mode and needs to send non-cleartext IEs, it shall include the NAS message container IE as described in clause 4.4.6 [TS 24.501 §5.5.2.2.1].
>  - The UE starts the timer T3521 and enters the state 5GMM-DEREGISTERED-INITIATED [TS 24.501 §5.5.2.2.1].
> 
> 2. **Protection of Initial NAS Messages (DEREGISTRATION REQUEST):**
>  - If the UE has a valid 5G NAS security context and needs to send non-cleartext IEs in a DEREGISTRATION REQUEST message, the UE includes the entire DEREGISTRATION REQUEST message (containing both cleartext and non-cleartext IEs) in the NAS message container IE, ciphers the value part of the NAS message container IE, and sends the DEREGISTRATION REQUEST message containing the cleartext IEs and the NAS message container IE [TS 24.501 §4.4.6].
>  - If the UE does not need to send non-cleartext IEs in a DEREGISTRATION REQUEST message, it sends the DEREGISTRATION REQUEST message without including the NAS message container IE [TS 24.501 §4.4.6].
> 
> 3. **Abnormal Cases and State Transitions:**
>  - **Lower layer failure or release of N1 NAS signalling connection before receiving DEREGISTRATION ACCEPT:** The de-registration procedure is aborted. If it was performed due to disabling of 5GS services, the UE enters the **5GMM-NULL** state; if requested for reasons other than disabling 5GS services, the UE enters the **5GMM-DEREGISTERED** state [TS 24.501 §4.4.6].
>  - **Timer T3521 timeout:** 
>  - If performed based on conditions in 3GPP TS 23.122 [5] annex C, the procedure is aborted on expiry, the UE locally releases the established N1 NAS signalling connection, and enters the **5GMM-DEREGISTERED** state [TS 24.501 §4.4.6].
>  - Otherwise, the UE retransmits the DEREGISTRATION REQUEST message and restarts timer T3521 on the first four expiries. On the fifth expiry, the procedure is aborted: if due to disabling 5GS services, the UE enters the **5GMM-NULL** state; otherwise, it enters the **5GMM-DEREGISTERED** state [TS 24.501 §4.4.6].

**Rel-17** (§5.1.3.2.3.2, §5.5.2.2.1, §5.5.2.2.6):

> The UE initiates the de-registration procedure by sending a DEREGISTRATION REQUEST message [TS 24.501 §5.5.2.2.1]. 
> 
> The details of the procedure, states, and NAS messages involved are as follows:
> 
> * **Initiation and NAS Messages:**
>  - The UE-initiated de-registration procedure is started by sending the DEREGISTRATION REQUEST message [TS 24.501 §5.5.2.2.1].
>  - The De-registration type IE indicates whether the procedure is due to a "switch off" or not [TS 24.501 §5.5.2.2.1].
>  - The access type IE indicates whether the de-registration is for 5GS services over 3GPP access, non-3GPP access, or both when registered in the same PLMN over both accesses [TS 24.501 §5.5.2.2.1].
>  - The 5GS mobile identity IE is populated with a valid 5G-GUTI. If not available, it is populated with the SUCI (using timer T3519 management) or the PEI if neither 5G-GUTI nor SUCI is available [TS 24.501 §5.5.2.2.1].
> 
> * **State Transitions:**
>  - If the de-registration request is not due to switch off and the UE is in the state 5GMM-REGISTERED or 5GMM-REGISTERED-INITIATED, timer T3521 is started after sending the DEREGISTRATION REQUEST message, and the UE enters the state 5GMM-DEREGISTERED-INITIATED [TS 24.501 §5.5.2.2.1].
>  - Upon successful completion or specific abnormal cases (such as lower layer failure or expiry of timer T3521), if normal de-registration was requested for reasons other than disabling 5GS services, the UE enters the state 5GMM-DEREGISTERED [TS 24.501 §5.5.2.2.6]. (If due to disabling 5GS services, it enters 5GMM-NULL) [TS 24.501 §5.5.2.2.6].
>  - In the state 5GMM-DEREGISTERED, no 5GMM context has been established or the 5GMM context is marked as deregistered, and the UE is considered deregistered [TS 24.501 §5.1.3.2.3.2].

## x-07 — How are authentication and NAS security established between the UE and the AMF?

**Rel-18** (§4.4.1, §4.4.2.1.1, §4.4.2.5, §4.4.5):

> Before security can be activated, the AMF and the UE need to establish a 5G NAS security context [TS 24.501 §4.4.2.1.1]. 
> 
> * **Creation:** A 5G NAS security context is usually created as a result of a primary authentication and key agreement procedure between the AMF and the UE [TS 24.501 §4.4.2.1.1]. It may also be created during an N1 mode to N1 mode handover, or derived as a mapped 5G NAS security context from an EPS security context during an inter-system change from S1 mode to N1 mode when the AMF does not support interworking without N26 and the UE operates in single-registration mode [TS 24.501 §4.4.2.1.1].
> * **Taking into use:** The 5G NAS security context is taken into use by the UE and the AMF when the AMF initiates a security mode control procedure, during an N1 mode to N1 mode handover, or during the inter-system change procedure from S1 mode to N1 mode [TS 24.501 §4.4.2.1.1]. 
> * **Secure exchange of NAS messages:** 
>  - If the UE has a valid native 5G NAS security context, it applies security protection to the initial NAS message [TS 24.501 §4.4.2.5]. If verification of this message is successful, the AMF re-establishes the secure exchange of NAS messages by either replying with an integrity-protected and ciphered REGISTRATION ACCEPT message, or by initiating a security mode control procedure [TS 24.501 §4.4.2.5].
>  - If the UE has no valid native 5G NAS security context, it sends the REGISTRATION REQUEST message without integrity protection and encryption [TS 24.501 §4.4.2.5]. The AMF then triggers a primary authentication and key agreement procedure (or creates a mapped 5G NAS security context depending on N26 support and EPS security context algorithms), and initiates a security mode control procedure to take the newly created 5G NAS security context into use [TS 24.501 §4.4.2.5].
> * **Ciphering and Integrity:** The UE and AMF start ciphering and deciphering NAS messages when the secure exchange of NAS messages has been established for an N1 NAS signalling connection [TS 24.501 §4.4.5]. The use of ciphering is an operator option subject to AMF configuration, and networks without ciphering use the "null ciphering algorithm" 5G-EA0 [TS 24.501 §4.4.1][TS 24.501 §4.4.5].

**Rel-17** (§4.4.2.1, §4.4.2.5, §4.4.2.6, §5.4.2.1):

> Before security can be activated, the AMF and the UE need to establish a 5G NAS security context, which is usually created as the result of a primary authentication and key agreement procedure between the AMF and the UE [TS 24.501 §4.4.2.1]. A new 5G NAS security context may also be created during an N1 mode to N1 mode handover, or during an inter-system change from S1 mode to N1 mode by deriving a mapped 5G NAS security context from an EPS security context [TS 24.501 §4.4.2.1].
> 
> The establishment of secure exchange of NAS messages typically follows these principles:
> - **During the Registration Procedure:** Secure exchange of NAS messages is usually established by the AMF initiating a security mode control procedure [TS 24.501 §4.4.2.5]. 
> - **During Inter-System Change from S1 mode to N1 mode (5GMM-CONNECTED mode):** Secure exchange is established by:
>  1. Transmitting NAS security related parameters encapsulated in AS signalling from the AMF to the UE triggering the inter-system change, which the UE uses to generate a mapped 5G NAS security context [TS 24.501 §4.4.2.5].
>  2. Transmitting a REGISTRATION REQUEST message from the UE to the AMF (integrity protected using the mapped 5G NAS security context), followed either by the AMF taking the native 5G NAS security context into use via a security mode control procedure or taking the mapped 5G NAS security context into use [TS 24.501 §4.4.2.5].
> - **During Inter-System Change from S1 mode to N1 mode (5GMM-IDLE mode):** 
>  - If the UE has a valid native 5G NAS security context, it transmits a REGISTRATION REQUEST message integrity protected with it [TS 24.501 §4.4.2.5]. Upon successful verification, the AMF replies with a REGISTRATION ACCEPT message protected using the native 5G NAS security context or initiates a security mode control procedure [TS 24.501 §4.4.2.5].
>  - If the UE has no valid native 5G NAS security context, it sends the REGISTRATION REQUEST message without protection, after which the AMF either triggers a primary authentication and key agreement procedure or creates a mapped 5G NAS security context depending on support for the N26 interface and EPS security algorithms [TS 24.501 §4.4.2.5]. The newly created context is then taken into use by initiating a security mode control procedure [TS 24.501 §4.4.2.5].
> - **During N1 mode to N1 mode Handover:** Secure exchange is established via NAS security related parameters sent in AS signalling from the target AMF to the UE, allowing the UE to create a new 5G NAS security context while continuing the secure exchange [TS 24.501 §4.4.2.5].
> 
> **NAS Signalling and Security Mode Control Procedure:**
> - The purpose of the NAS security mode control procedure is to take a 5G NAS security context into use, and initialize and start NAS signalling security between the UE and the AMF with corresponding keys and algorithms [TS 24.501 §5.4.2.1].
> - When the AMF initiates a re-authentication to create a new 5G NAS security context, current security is used until the AMF initiates a security mode control procedure [TS 24.501 §4.4.2.6].
> - The AMF sends a **SECURITY MODE COMMAND** message containing the ngKSI of the new or modified 5G NAS security context and a set of selected NAS security algorithms [TS 24.501 §4.4.2.6]. The **SECURITY MODE COMMAND** message is sent integrity protected with the new/modified 5G NAS security context, but unciphered [TS 24.501 §4.4.2.6].
> - When the UE responds with a **SECURITY MODE COMPLETE** message, it sends the message integrity protected and ciphered with the new or modified 5G NAS security context [TS 24.501 §4.4.2.6].

