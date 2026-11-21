# Test set review

Status: **0/30 verified**. Gold sections and reference answers were drafted from `data/processed/chunks.jsonl` (searched, not recalled). For each item, check the question, the gold section(s) and the reference answer against the excerpt, then set `"verified": true` in `eval/testset.json` (or fix the item).

Hit rule used by the evaluation: a retrieved chunk matches when its section equals a gold section or is a sub-clause of it (same spec). Cross questions additionally need at least one hit per gold spec.

Gold-section existence check: OK

## s23-01 (simple) — NOT verified

**Q:** What is the role of the AMF in the 5G System?

- **TS 23.501** gold: §6.2.1

**Reference answer:** The AMF includes, among others: termination of the RAN CP interface (N2); termination of NAS (N1), NAS ciphering and integrity protection; registration management; connection management; reachability management; mobility management; lawful intercept for AMF events; transport for SM messages between UE and SMF and transparent proxy for routing SM messages; access authentication and access authorization; transport for SMS messages between UE and SMSF; Security Anchor Functionality (SEAF); location services management and EPS Bearer ID allocation for interworking with EPS. Some or all of these functionalities may be supported in a single AMF instance.

<details><summary>Excerpt TS 23.501 §6.2.1 — <code>23.501:6.2.1:0</code></summary>

> The Access and Mobility Management function (AMF) includes the following functionality. Some or all of the AMF functionalities may be supported in a single instance of an AMF:
> - Termination of RAN CP interface (N2).
> - Termination of NAS (N1), NAS ciphering and integrity protection.
> - Registration management.
> - Connection management.
> - Reachability management.
> - Mobility Management.
> - Lawful intercept (for AMF events and interface to LI System).
> - Provide transport for SM messages between UE and SMF.
> - Transparent proxy for routing SM messages.
> - Access Authentication.
> - Access Authorization.
> - Provide transport for SMS messages between UE and SMSF.
> - Security Anchor Functionality (SEAF) as specified in TS 33.501 [29].
> - Location Services management for regulatory services.
> - Provide transport for Location Services messages between UE and LMF as well as between RAN and LMF.
> - EPS Bearer I

</details>

## s23-02 (simple) — NOT verified

**Q:** Which functionalities does the SMF provide?

- **TS 23.501** gold: §6.2.2

**Reference answer:** The SMF includes session management (session establishment, modification and release, including tunnel maintenance between UPF and AN node), UE IP address allocation and management (including optional authorization), DHCPv4 and DHCPv6 server and client functions, responding to ARP / IPv6 Neighbour Solicitation requests for Ethernet PDUs, selection and control of the UP function, and configuration of traffic steering at the UPF to route traffic to the proper destination.

<details><summary>Excerpt TS 23.501 §6.2.2 — <code>23.501:6.2.2:0</code></summary>

> Management e.g. Session Establishment, modify and release, including tunnel maintain between UPF and AN node.
> - UE IP address allocation & management (including optional Authorization). The UE IP address may be received from a UPF or from an external data network.
> - DHCPv4 (server and client) and DHCPv6 (server and client) functions.
> - Functionality to respond to Address Resolution Protocol (ARP) requests and / or IPv6 Neighbour Solicitation requests based on local cache information for the Ethernet PDUs. The SMF responds to the ARP and / or the IPv6 Neighbour Solicitation Request by providing the MAC address corresponding to the IP address sent in the request.
> - Selection and control of UP function, including controlling the UPF to proxy ARP or IPv6 Neighbour Discovery, or to forward all ARP/IPv6 Neighbour Solicitation traffic to the SMF, for Ethernet PDU Sessions.
> - Configures traffic 

</details>

## s23-03 (simple) — NOT verified

**Q:** What functionality does the UPF support?

- **TS 23.501** gold: §6.2.3

**Reference answer:** The UPF includes: anchor point for intra-/inter-RAT mobility; allocation of UE IP address/prefix in response to SMF request; external PDU Session point of interconnect to the Data Network; packet routing and forwarding; packet inspection; the user plane part of policy rule enforcement (gating, redirection, traffic steering); lawful intercept (UP collection); traffic usage reporting; QoS handling for the user plane (UL/DL rate enforcement, reflective QoS marking in DL); uplink traffic verification (SDF to QoS Flow mapping); transport level packet marking; downlink packet buffering and downlink data notification triggering; and sending of end marker(s) to the source NG-RAN node.

<details><summary>Excerpt TS 23.501 §6.2.3 — <code>23.501:6.2.3:0</code></summary>

> point for Intra-/Inter-RAT mobility (when applicable).
> - Allocation of UE IP address/prefix (if supported) in response to SMF request.
> - External PDU Session point of interconnect to Data Network.
> - Packet routing & forwarding (e.g. support of Uplink classifier to route traffic flows to an instance of a data network, support of Branching point to support multi-homed PDU Session, support of traffic forwarding within a 5G VN group (UPF local switching, via N6, via N19)).
> - Packet inspection (e.g. Application detection based on service data flow template and the optional PFDs received from the SMF in addition).
> - User Plane part of policy rule enforcement, e.g. Gating, Redirection, Traffic steering).
> - Lawful intercept (UP collection).
> - Traffic usage reporting.
> - QoS handling for user plane, e.g. UL/DL rate enforcement, Reflective QoS marking in DL.
> - Uplink Traffic verification (SDF to Qo

</details>

## s23-04 (simple) — NOT verified

**Q:** What is the role of the NSSF?

- **TS 23.501** gold: §6.2.14

**Reference answer:** The Network Slice Selection Function selects the set of Network Slice instances serving the UE, determines the Allowed NSSAI and the Configured NSSAI (and if needed their mapping to the Subscribed S-NSSAIs), and determines the AMF Set to be used to serve the UE or a list of candidate AMF(s), possibly by querying the NRF. It may also support Network Slice (instance) restriction based on NWDAF analytics and determine whether an S-NSSAI has to be replaced by an Alternative S-NSSAI.

<details><summary>Excerpt TS 23.501 §6.2.14 — <code>23.501:6.2.14:0</code></summary>

> The Network Slice Selection Function (NSSF) supports the following functionality:
> - Selecting the set of Network Slice instances serving the UE;
> - Determining the Allowed NSSAI and, if needed, the mapping to the Subscribed S-NSSAIs;
> - Determining the Configured NSSAI and, if needed, the mapping to the Subscribed S-NSSAIs;
> - Determining the AMF Set to be used to serve the UE, or, based on configuration, a list of candidate AMF(s), possibly by querying the NRF;
> - The NSSF may provide support for Network Slice restriction and Network Slice instance restriction based on NWDAF analytics.
> - Determining whether an S-NSSAI has to be replaced and providing to the AMF the indication that the S-NSSAI is unavailable and a corresponding Alternative S-NSSAI, e.g. based on received NWDAF analytics (e.g. for Service Experience for a Network Slice or Slice load level), or local trigger from the OAM syste

</details>

## s23-05 (simple) — NOT verified

**Q:** Which reference point connects the SMF and the UPF, and which one connects the (R)AN and the AMF?

- **TS 23.501** gold: §4.2.7

**Reference answer:** N4 is the reference point between the SMF and the UPF; N2 is the reference point between the (R)AN and the AMF. (For context: N1 is between the UE and the AMF, N3 between the (R)AN and the UPF, N6 between the UPF and a Data Network, N9 between two UPFs.)

<details><summary>Excerpt TS 23.501 §4.2.7 — <code>23.501:4.2.7:0</code></summary>

> the AMF.
> N3: Reference point between the (R)AN and the UPF.
> N4: Reference point between the SMF and the UPF.
> N6: Reference point between the UPF and a Data Network.
> N9: Reference point between two UPFs.
> The following reference points show the interactions that exist between the NF services in the NFs. These reference points are realized by corresponding NF service-based interfaces and by specifying the identified consumer and producer NF service as well as their interaction in order to realize a particular system procedure.
> N5: Reference point between the PCF and an AF or TSN AF.
> N7: Reference point between the SMF and the PCF.
> N8: Reference point between the UDM and the AMF.
> N10: Reference point between the UDM and the SMF.
> N11: Reference point between the AMF and the SMF.
> N12: Reference point between AMF and AUSF.
> N13: Reference point between the UDM and Authentication Server function 

</details>

## s23-06 (simple) — NOT verified

**Q:** What is a QoS Flow and how is it identified in the 5G System?

- **TS 23.501** gold: §5.7.1.1

**Reference answer:** The QoS Flow is the finest granularity of QoS differentiation in the PDU Session. It is identified by a QoS Flow ID (QFI); user plane traffic with the same QFI within a PDU Session receives the same traffic forwarding treatment. The QFI is carried in an encapsulation header on N3 (and N9), is unique within a PDU Session and may be dynamically assigned or equal to the 5QI. QoS Flows can be GBR or Non-GBR and are controlled by the SMF.

<details><summary>Excerpt TS 23.501 §5.7.1.1 — <code>23.501:5.7.1.1:0</code></summary>

> QoS Flows) and QoS Flows that do not require guaranteed flow bit rate (Non-GBR QoS Flows). The 5G QoS model also supports Reflective QoS (see clause 5.7.5).
> The QoS Flow is the finest granularity of QoS differentiation in the PDU Session. A QoS Flow ID (QFI) is used to identify a QoS Flow in the 5G System. User Plane traffic with the same QFI within a PDU Session receives the same traffic forwarding treatment (e.g. scheduling, admission threshold). The QFI is carried in an encapsulation header on N3 (and N9) i.e. without any changes to the e2e packet header. QFI shall be used for all PDU Session Types. The QFI shall be unique within a PDU Session. The QFI may be dynamically assigned or may be equal to the 5QI (see clause 5.7.2.1).
> Within the 5GS, a QoS Flow is controlled by the SMF and may be preconfigured, or established via the PDU Session Establishment procedure (see clause 4.3.2 of T

</details>

## s23-07 (simple) — NOT verified

**Q:** What are the standardized QoS characteristics of 5QI value 1?

- **TS 23.501** gold: §5.7.4

**Reference answer:** In Table 5.7.4-1, 5QI 1 has resource type GBR, default priority level 20, packet delay budget 100 ms, packet error rate 10^-2, default maximum data burst volume N/A, default averaging window 2000 ms, and the example service is Conversational Voice.

<details><summary>Excerpt TS 23.501 §5.7.4 — <code>23.501:5.7.4:4</code></summary>

> Table 5.7.4-1: Standardized 5QI to QoS characteristics mapping
> | 5QI Value | Resource Type | Default Priority Level | Packet Delay Budget (NOTE 3) | Packet Error Rate | Default Maximum Data Burst Volume (NOTE 2) | Default Averaging Window | Example Services |
> |---|---|---|---|---|---|---|---|
> | NOTE 1: A packet which is delayed more than PDB is not counted as lost, thus not included in the PER. NOTE 2: It is required that default MDBV is supported by a PLMN supporting the related 5QIs. NOTE 3: The Maximum Transfer Unit (MTU) size considerations in clause 9.3 and Annex J are also applicable. IP fragmentation may have impacts to CN PDB and details are provided in clause 5.6.10. NOTE 4: A static value for the CN PDB of 1 ms for the delay between a UPF terminating N6 and a 5G-AN should be subtracted from a given PDB to derive the packet delay budget that applies to the radio interface. When 

</details>

## s23-08 (simple) — NOT verified

**Q:** What does an S-NSSAI consist of?

- **TS 23.501** gold: §5.15.2.1

**Reference answer:** An S-NSSAI identifies a Network Slice and is comprised of a Slice/Service type (SST), which refers to the expected Network Slice behaviour in terms of features and services, and a Slice Differentiator (SD), which is optional information complementing the SST to differentiate amongst multiple Network Slices of the same SST.

<details><summary>Excerpt TS 23.501 §5.15.2.1 — <code>23.501:5.15.2.1:0</code></summary>

> S-NSSAI identifies a Network Slice.
> An S-NSSAI is comprised of:
> - A Slice/Service type (SST), which refers to the expected Network Slice behaviour in terms of features and services;
> - A Slice Differentiator (SD), which is optional information that complements the Slice/Service type(s) to differentiate amongst multiple Network Slices of the same Slice/Service type.
> An S-NSSAI can have standard values (i.e. such S-NSSAI is only comprised of an SST with a standardised SST value, see clause 5.15.2.2 and no SD) or non-standard values (i.e. such S-NSSAI is comprised of either both an SST and an SD or only an SST without a standardised SST value and no SD). An S-NSSAI with a non-standard value identifies a single Network Slice within the PLMN with which it is associated. An S-NSSAI with a non-standard value shall not be used by the UE in access stratum procedures in any PLMN other than the one 

</details>

## s23-09 (simple) — NOT verified

**Q:** What characterizes SSC mode 1?

- **TS 23.501** gold: §5.6.9.2.1

**Reference answer:** For a PDU Session of SSC mode 1, the UPF acting as PDU Session Anchor at establishment is maintained regardless of the access technology the UE successively uses. For IPv4, IPv6 or IPv4v6 PDU Sessions, IP continuity is supported regardless of UE mobility events. SSC mode 1 may apply to any PDU Session type and any access type, and a UE supporting PDU Connectivity shall support SSC mode 1.

<details><summary>Excerpt TS 23.501 §5.6.9.2.1 — <code>23.501:5.6.9.2.1:0</code></summary>

> For a PDU Session of SSC mode 1, the UPF acting as PDU Session Anchor at the establishment of the PDU Session is maintained regardless of the access technology (e.g. Access Type and cells) a UE is successively using to access the network.
> In the case of a PDU Session of IPv4 or IPv6 or IPv4v6 type, IP continuity is supported regardless of UE mobility events.
> In this Release of the specification, when IPv6 multihoming or UL CL applies to a PDU Session of in SSC mode 1 and the network allocates (based on local policies) additional PDU Session Anchors to such a PDU Session, these additional PDU Session Anchors may be released or allocated and the UE does not expect that the additional IPv6 prefix is maintained during the lifetime of PDU Session.
> SSC mode 1 may apply to any PDU Session type and to any access type.
> A UE supporting PDU Connectivity shall support SSC mode 1.

</details>

## s23-10 (simple) — NOT verified

**Q:** How does the AMF allocate a registration area to a UE over 3GPP access?

- **TS 23.501** gold: §5.3.2.3

**Reference answer:** Registration area management allocates and reallocates a registration area per access type. When a UE registers over 3GPP access, the AMF allocates a set of tracking areas in a TAI List to the UE, and may take into account information such as the Mobility Pattern and Allowed/Non-Allowed Area. An AMF whose serving area is the whole PLMN may allocate the whole PLMN as registration area to a UE in MICO mode. The 5G System supports allocating a registration area using a single TAI List that includes tracking areas of any NG-RAN nodes in the registration area.

<details><summary>Excerpt TS 23.501 §5.3.2.3 — <code>23.501:5.3.2.3:0</code></summary>

> access.
> When a UE registers with the network over the 3GPP access, the AMF allocates a set of tracking areas in TAI List to the UE. When the AMF allocates registration area, i.e. the set of tracking areas in TAI List, to the UE it may take into account various information (e.g. Mobility Pattern and Allowed/Non-Allowed Area (refer to clause 5.3.4.1)). An AMF which has the whole PLMN as serving area may alternatively allocate the whole PLMN ("all PLMN") as registration area to a UE in MICO mode (refer to clause 5.4.1.3). When AMF allocates registration area for UE registered for Disaster Roaming service as specified in clause 5.40.4, AMF shall only consider TAIs covering the area with the Disaster Condition.
> The 5G System shall support allocating a Registration Area using a single TAI List which includes tracking areas of any NG-RAN nodes in the Registration Area for a UE.
> In the case of S

</details>

## s24-01 (simple) — NOT verified

**Q:** What does cause #9 mean in 5GMM?

- **TS 24.501** gold: §A.1

**Reference answer:** 5GMM cause #9 is "UE identity cannot be derived by the network". It is sent to the UE when the network cannot derive the UE's identity from the 5G-GUTI or 5G-S-TMSI, e.g. because of no matching identity/context in the network or failure to validate the UE's identity due to integrity check failure of the received message.

<details><summary>Excerpt TS 24.501 §A.1 — <code>24.501:A.1:0</code></summary>

> Cause #3 – Illegal UE
> - This 5GMM cause is sent to the UE when the network refuses service to the UE either because an identity of the UE is not acceptable to the network or because the UE does not pass the authentication check.
> Cause #6 – Illegal ME
> - This 5GMM cause is sent to the UE if the ME used is not acceptable to the network, e.g. on the prohibited list.
> Cause #9 – UE identity cannot be derived by the network.
> - This 5GMM cause is sent to the UE when the network cannot derive the UE's identity from the 5G-GUTI or 5G-S-TMSI because of e.g. no matching identity/context in the network, failure to validate the UE's identity due to integrity check failure of the received message.
> Cause #10 – Implicitly de-registered
> - This 5GMM cause is sent to the UE either if the network has implicitly de-registered the UE, e.g. after the implicit de-registration timer has expired, or if the 5GMM co

</details>

## s24-02 (simple) — NOT verified

**Q:** What does 5GMM cause #22 indicate?

- **TS 24.501** gold: §A.3

**Reference answer:** 5GMM cause #22 is "Congestion": it is sent to the UE because of congestion in the network (e.g. no channel, facility busy/congested).

<details><summary>Excerpt TS 24.501 §A.3 — <code>24.501:A.3:0</code></summary>

> Cause #20 – MAC failure
> - This 5GMM cause is sent to the network if the USIM detects that the MAC in the AUTHENTICATION REQUEST message is not fresh.
> Cause #21 – Synch failure
> - This 5GMM cause is sent to the network if the USIM detects that the SQN in the AUTHENTICATION REQUEST message is out of range.
> Cause #22 – Congestion
> - This 5GMM cause is sent to the UE because of congestion in the network (e.g. no channel, facility busy/congested etc.).
> Cause #23 – UE security capabilities mismatch
> - This 5GMM cause is sent to the network if the UE detects that the UE security capability does not match the one sent back by the network.
> Cause #24 – Security mode rejected, unspecified
> - This 5GMM cause is sent to the network if the security mode command is rejected by the UE for unspecified reasons.
> Cause #26 – Non-5G authentication unacceptable
> - This 5GMM cause is sent to the network in N1 mode 

</details>

## s24-03 (simple) — NOT verified

**Q:** What does 5GSM cause #27 indicate?

- **TS 24.501** gold: §B.1

**Reference answer:** 5GSM cause #27 is "Missing or unknown DNN": it is used by the network to indicate that the requested service was rejected by the external DN because the DNN was not included although required, or because the DNN could not be resolved. (Not to be confused with 5GMM cause #27 "N1 mode not allowed".)

<details><summary>Excerpt TS 24.501 §B.1 — <code>24.501:B.1:0</code></summary>

> Cause #8 – Operator Determined Barring
> - This 5GSM cause is used by the network to indicate that the requested service was rejected by the SMF due to Operator Determined Barring.
> Cause #26 – Insufficient resources
> - This 5GSM cause is used by the UE or by the network to indicate that the requested service cannot be provided due to insufficient resources.
> Cause #27 – Missing or unknown DNN
> - This 5GSM cause is used by the network to indicate that the requested service was rejected by the external DN because the DNN was not included although required or if the DNN could not be resolved.
> Cause #28 – Unknown PDU session type
> - This 5GSM cause is used by the network to indicate that the requested service was rejected by the external DN because the requested PDU session type could not be recognised or is not allowed.
> Cause #29 – User authentication or authorization failed
> - This 5GSM cause is 

</details>

## s24-04 (simple) — NOT verified

**Q:** When is timer T3510 started and stopped, and what happens when it expires?

- **TS 24.501** gold: §10.2, §5.5.1.2.7, §5.5.1.3.7, §5.5.1.2.2

**Reference answer:** T3510 (15 s; 85 s in WB-N1/CE mode; 27 s for access via a satellite NG-RAN cell) runs in state 5GMM-REGISTERED-INITIATED. It is started on transmission of the REGISTRATION REQUEST message and stopped when a REGISTRATION ACCEPT or REGISTRATION REJECT message is received. On expiry the UE starts T3511 or T3502 as specified in clause 5.5.1.2.7 (initial registration) or 5.5.1.3.7 (mobility and periodic registration update); in the T3510 timeout abnormal case of initial registration the UE aborts the registration procedure (subject to the conditions listed there).

<details><summary>Excerpt TS 24.501 §10.2 — <code>24.501:10.2:1</code></summary>

> the registration procedure, if still required |
> | T3510 | 15s NOTE 7 NOTE 8 In WB-N1/CE mode, 85s For access via a satellite NG-RAN cell, 27s NOTE 12 | 5GMM-REGISTERED-INITIATED | Transmission of REGISTRATION REQUEST message | REGISTRATION ACCEPT message received or REGISTRATION REJECT message received | Start T3511 or T3502 as specified in clause 5.5.1.2.7 if T3510 expired during registration procedure for initial registration. Start T3511 or T3502 as specified in clause 5.5.1.3.7 if T3510 expired during the registration procedure for mobility and periodic registration update |
> | T3511 | 10s | 5GMM-DEREGISTERED.ATTEMPTING-REGISTRATION 5GMM-REGISTERED.ATTEMPTING-REGISTRATION-UPDATE 5GMM-REGISTERED.NORMAL-SERVICE or 5GMM-REGISTERED.NON-ALLOWED-SERVICE | At registration failure due to lower layer failure, T3510 timeout or registration rejected with other 5GMM cause values than those treate

</details>

<details><summary>Excerpt TS 24.501 §5.5.1.2.7 — <code>24.501:5.5.1.2.7:2</code></summary>

> and
>   - 2) otherwise, the registration procedure for initial registration shall be aborted and the registration procedure for mobility registration update shall be initiated.
> - If a 5G-GUTI was allocated during the registration procedure, this 5G-GUTI shall be used in the registration procedure.
> - i) Transmission failure of REGISTRATION COMPLETE message indication with change in the current TAI.
>   - 1) If the current TAI is still part of the TAI list, the UE resends the REGISTRATION COMPLETE message to the network; and
>   - 2) otherwise, the registration procedure for initial registration shall be aborted and the registration procedure for mobility registration update shall be initiated.
> - j) Transmission failure of REGISTRATION COMPLETE message indication without change in the current TAI from lower layers.
> - It is up to the UE implementation how to re-run the ongoing procedure.
> - k) Tra

</details>

<details><summary>Excerpt TS 24.501 §5.5.1.3.7 — <code>24.501:5.5.1.3.7:2</code></summary>

> registration procedure for mobility and periodic registration update is completed, the registration procedure for mobility and periodic registration update shall be aborted and re-initiated immediately. The UE shall set the 5GS update status to 5U2 NOT UPDATED.
> - g) Registration procedure for mobility and periodic registration update and de-registration procedure collision.
> - If the UE receives a DEREGISTRATION REQUEST message without 5GMM cause value #11, #12, #13 or #15 before the registration procedure for mobility and periodic registration update has been completed, the registration procedure for mobility and periodic registration update shall be aborted and the de-registration procedure shall be progressed.
> - If the UE receives a DEREGISTRATION REQUEST message with 5GMM cause value #11, #12, #13 or #15 before the registration procedure for mobility and periodic registration update h

</details>

<details><summary>Excerpt TS 24.501 §5.5.1.2.2 — <code>24.501:5.5.1.2.2:0</code></summary>

> The UE in state 5GMM-DEREGISTERED shall initiate the registration procedure for initial registration by sending a REGISTRATION REQUEST message to the AMF,
> - a) when the UE performs initial registration for 5GS services;
> - b) when the UE performs initial registration for emergency services;
> - c) when the UE performs initial registration for SMS over NAS;
> - d) when the UE moves from GERAN to NG-RAN coverage or the UE moves from a UTRAN to NG-RAN coverage and the following applies:
>   - 1) the UE initiated a GPRS attach or routing area updating procedure while in A/Gb mode or Iu mode; or
>   - 2) the UE has performed 5G-SRVCC from NG-RAN to UTRAN as specified in 3GPP TS 23.216 [6A],
> - and since then the UE did not perform a successful EPS attach or tracking area updating procedure in S1 mode or registration procedure in N1 mode;
> - e) when the UE performs initial registration for onboarding ser

</details>

## s24-05 (simple) — NOT verified

**Q:** What is the default value of timer T3502 and when is it started?

- **TS 24.501** gold: §10.2

**Reference answer:** T3502 has a default value of 12 minutes. It is started at registration failure when the registration attempt counter is equal to 5, is stopped on transmission of a REGISTRATION REQUEST message, and on expiry the UE initiates the registration procedure, if still required.

<details><summary>Excerpt TS 24.501 §10.2 — <code>24.501:10.2:9</code></summary>

> services, the value of this timer is set equal to the value of timer T3512. If the T3346 value provided in the mobility management messages is greater than the value of the timer T3512, the AMF sets the mobile reachable timer and the implicit de-registration timer such that the sum of the timer values is greater than the value of timer T3346. NOTE 2: The value of this timer is network dependent. If MICO is activated, the default value of this timer is 4 minutes greater than the value of timer T3512. NOTE 3: The value of this timer is network dependent. The default value of this timer is 4 minutes greater than the non-3GPP de-registration timer. If the T3346 value provided in the mobility management messages is greater than the value of the non-3GPP de-registration timer, the AMF sets the non-3GPP implicit de-registration timer value to be 8 minutes greater than the value of timer T3346. 

</details>

## s24-06 (simple) — NOT verified

**Q:** Which mandatory information elements does the REGISTRATION REQUEST message contain?

- **TS 24.501** gold: §8.2.6.1

**Reference answer:** According to Table 8.2.6.1.1, the mandatory (M) IEs of REGISTRATION REQUEST (sent by the UE to the AMF) are: Extended protocol discriminator, Security header type, Spare half octet, Registration request message identity, 5GS registration type, ngKSI (NAS key set identifier) and 5GS mobile identity.

<details><summary>Excerpt TS 24.501 §8.2.6.1 — <code>24.501:8.2.6.1:1</code></summary>

> Table 8.2.6.1.1: REGISTRATION REQUEST message content
> | IEI | Information Element | Type/Reference | Presence | Format | Length |
> |---|---|---|---|---|---|
> |  | Extended protocol discriminator | Extended Protocol discriminator 9.2 | M | V | 1 |
> |  | Security header type | Security header type 9.3 | M | V | 1/2 |
> |  | Spare half octet | Spare half octet 9.5 | M | V | 1/2 |
> |  | Registration request message identity | Message type 9.7 | M | V | 1 |
> |  | 5GS registration type | 5GS registration type 9.11.3.7 | M | V | 1/2 |
> |  | ngKSI | NAS key set identifier 9.11.3.32 | M | V | 1/2 |
> |  | 5GS mobile identity | 5GS mobile identity 9.11.3.4 | M | LV-E | 6-n |
> | C- | Non-current native NAS key set identifier | NAS key set identifier 9.11.3.32 | O | TV | 1 |
> | 10 | 5GMM capability | 5GMM capability 9.11.3.1 | O | TLV | 3-15 |
> | 2E | UE security capability | UE security capability 9.11.3.54 | O

</details>

## s24-07 (simple) — NOT verified

**Q:** Which registration types can be indicated in the 5GS registration type information element?

- **TS 24.501** gold: §9.11.3.7

**Reference answer:** The 5GS registration type value (octet 1, bits 1 to 3) can be: initial registration (001), mobility registration updating (010), periodic registration updating (011), emergency registration (100), SNPN onboarding registration (101), disaster roaming mobility registration updating (110) and disaster roaming initial registration (111). Other values are interpreted as initial registration by the network. Bit 4 is the follow-on request (FOR) bit.

<details><summary>Excerpt TS 24.501 §9.11.3.7 — <code>24.501:9.11.3.7:0</code></summary>

> coded as shown in figure 9.11.3.7.1 and table 9.11.3.7.1.
> The 5GS registration type is a type 1 information element with a length of 1 octet.
> | 8 | 7 | 6 | 5 | 4 | 3 | 2 | 1 |  |
> |---|---|---|---|---|---|---|---|---|
> | 5GS registration type IEI | 5GS registration type IEI | 5GS registration type IEI | 5GS registration type IEI | FOR | 5GS registration type value | 5GS registration type value | 5GS registration type value | octet 1 |
> [Figure: Figure 9.11.3.7.1: 5GS registration type information element]
> Table 9.11.3.7.1: 5GS registration type information element
> | 5GS registration type value (octet 1, bits 1 to 3) |  |  |  |  |
> |---|---|---|---|---|
> | Bits |  |  |  |  |
> | 3 | 2 | 1 |  |  |
> | 0 | 0 | 1 |  | initial registration |
> | 0 | 1 | 0 |  | mobility registration updating |
> | 0 | 1 | 1 |  | periodic registration updating |
> | 1 | 0 | 0 |  | emergency registration |
> | 1 | 0 | 1 |  | SNP

</details>

## s24-08 (simple) — NOT verified

**Q:** What is the purpose of the service request procedure?

- **TS 24.501** gold: §5.6.1.1

**Reference answer:** The service request procedure is used to: (a) change the 5GMM mode from 5GMM-IDLE to 5GMM-CONNECTED mode; (b) request the establishment of user-plane resources for PDU sessions established without user-plane resources (when the UE is not using control plane CIoT 5GS optimization); or (c) initiate transfer of user data via the control plane when the UE uses control plane CIoT 5GS optimization and is in 5GMM-IDLE mode.

<details><summary>Excerpt TS 24.501 §5.6.1.1 — <code>24.501:5.6.1.1:0</code></summary>

> The purpose of the service request procedure is to:
> - a) change the 5GMM mode from 5GMM-IDLE to 5GMM-CONNECTED mode;
> - b) request the establishment of user-plane resources for PDU sessions which are established without user-plane resources if the UE is not using 5GS services with control plane CIoT 5GS optimization and the 5GMM mode is the 5GMM-IDLE mode or the 5GMM-CONNECTED mode; or
> - c) initiate transfer of user data via the control plane if the UE is using 5GS services with control plane CIoT 5GS optimization and the 5GMM mode is 5GMM-IDLE mode.
> NOTE 1: The lower layer indicates when the user-plane resources for PDU sessions are successfully established or released.
> This procedure is used when:
> - the network has downlink signalling pending over 3GPP access and the UE is in 5GMM-IDLE mode over 3GPP access;
> - the network has downlink signalling pending over non-3GPP access, the UE is i

</details>

## s24-09 (simple) — NOT verified

**Q:** What does the UE do when it accepts a SECURITY MODE COMMAND message?

- **TS 24.501** gold: §5.4.2.3

**Reference answer:** The UE checks the message by performing its integrity check and verifying that the Replayed UE security capabilities IE was not altered. If it can be accepted, the UE takes the indicated 5G NAS security context into use, ciphers the SECURITY MODE COMPLETE message with the selected ciphering algorithm (security header type "integrity protected and ciphered with new 5G NAS security context"), and from then on ciphers and integrity protects all NAS signalling messages with the selected algorithms.

<details><summary>Excerpt TS 24.501 §5.4.2.3 — <code>24.501:5.4.2.3:3</code></summary>

> identifier IE, then the UE shall check whether the SECURITY MODE COMMAND message indicates the ngKSI of the current 5GS security context, if it is a mapped 5G NAS security context, in order not to re-generate the K'AMF.
> Furthermore, if the SECURITY MODE COMMAND message can be accepted, the UE shall cipher the SECURITY MODE COMPLETE message with the selected 5GS ciphering algorithm and the 5GS NAS ciphering key based on the KAMF or mapped K'AMF indicated by the ngKSI. The UE shall set the security header type of the message to "integrity protected and ciphered with new 5G NAS security context".
> From this time onward the UE shall cipher and integrity protect all NAS signalling messages with the selected 5GS integrity and ciphering algorithms.
> If the AMF indicated in the SECURITY MODE COMMAND message that the IMEISV is requested and:
> - a) if the UE:
>   - 1) supports at least one 3GPP access 

</details>

## s24-10 (simple) — NOT verified

**Q:** How does the UE initiate a UE-initiated de-registration procedure?

- **TS 24.501** gold: §5.5.2.2.1

**Reference answer:** The UE sends a DEREGISTRATION REQUEST message. Its De-registration type IE indicates whether the de-registration is due to a "switch off" or not, and the access type indicates whether it applies to 3GPP access, non-3GPP access or both. The UE populates the 5GS mobile identity IE with its valid 5G-GUTI (or its SUCI if it has none), and enters state 5GMM-DEREGISTERED-INITIATED. If the UE is to be switched off, it tries for a period of 5 seconds to send the DEREGISTRATION REQUEST message.

<details><summary>Excerpt TS 24.501 §5.5.2.2.1 — <code>24.501:5.5.2.2.1:0</code></summary>

> SUCI sent in the DEREGISTRATION REQUEST message; and
> - b) if timer T3519 is running, send a DEREGISTRATION REQUEST message with the stored SUCI.
> If the UE does not have a valid 5G-GUTI and it does not have a valid SUCI, then the UE shall populate the 5GS mobile identity IE with its PEI.
> NOTE 2: During the initial registration for emergency services when the UE (with no USIM or invalid USIM) is in 5GMM-REGISTERED-INITIATED state, the UE has neither a valid 5G-GUTI nor a valid SUCI.
> If the de-registration request is not due to switch off and the UE is in the state 5GMM-REGISTERED or 5GMM-REGISTERED-INITIATED, timer T3521 shall be started in the UE after the DEREGISTRATION REQUEST message has been sent. The UE shall enter the state 5GMM-DEREGISTERED-INITIATED.
> If the UE is to be switched off, the UE shall try for a period of 5 seconds to send the DEREGISTRATION REQUEST message. During this 

</details>

## x-01 (cross) — NOT verified

**Q:** Describe the registration procedure and the NAS messages exchanged between the UE and the AMF.

- **TS 23.501** gold: §5.3.2
- **TS 24.501** gold: §5.5.1.2

**Reference answer:** TS 23.501: a UE needs to register with the network to receive services requiring registration and then updates its registration periodically (Periodic Registration Update) or upon mobility (Mobility Registration Update); initial registration involves network access control (user authentication and access authorization based on subscription in UDM), and the serving AMF is registered in UDM. TS 24.501: the UE in 5GMM-DEREGISTERED initiates initial registration by sending a REGISTRATION REQUEST message to the AMF (5GS registration type "initial registration") and starts T3510; if the request is accepted the AMF sends a REGISTRATION ACCEPT message; if it contains a 5G-GUTI the UE returns a REGISTRATION COMPLETE message to the AMF.

<details><summary>Excerpt TS 23.501 §5.3.2 — <code>23.501:5.3.2.1:0</code></summary>

> user needs to register with the network to receive services that requires registration. Once registered and if applicable the UE updates its registration with the network (see TS 23.502 [3]):
> - periodically, in order to remain reachable (Periodic Registration Update); or
> - upon mobility (Mobility Registration Update); or
> - to update its capabilities or re-negotiate protocol parameters (Mobility Registration Update).
> The Initial Registration procedure involves execution of Network Access Control functions as defined in clause 5.2 (i.e. user authentication and access authorization based on subscription profiles in UDM). As result of the Registration procedure, the identifier of the serving AMF serving the UE in the access through which the UE has registered will be registered in UDM.
> The registration management procedures are applicable over both 3GPP access and Non-3GPP access. The 3GPP a

</details>

<details><summary>Excerpt TS 24.501 §5.5.1.2 — <code>24.501:5.5.1.2.1:0</code></summary>

> This procedure can be used by a UE for initial registration for 5GS services.
> When the UE initiates the registration procedure for initial registration, the UE shall indicate "initial registration" in the 5GS registration type IE. When the UE initiates the registration procedure for emergency services, the UE shall indicate "emergency registration" in the 5GS registration type IE. When the UE initiates the initial registration for onboarding services in SNPN, the UE shall indicate "SNPN onboarding registration" in the 5GS registration type IE. When the UE initiates the initial registration procedure for disaster roaming services, the UE shall indicate "disaster roaming initial registration" in the 5GS registration type IE.
> If the MUSIM UE initiates the registration procedure for initial registration and indicates "emergency registration" in the 5GS registration type IE in the REGISTRATIO

</details>

## x-02 (cross) — NOT verified

**Q:** How is a PDU session established, and which 5GSM messages are exchanged?

- **TS 23.501** gold: §5.6.1
- **TS 24.501** gold: §6.4.1

**Reference answer:** TS 23.501: PDU Sessions provide the PDU Connectivity Service with a data network identified by a DNN; they are established upon UE request using NAS SM signalling exchanged over N1 between the UE and the SMF, and each supports a single PDU Session type (IPv4, IPv6, IPv4v6, Ethernet, Unstructured). TS 24.501: to initiate the UE-requested PDU session establishment procedure the UE creates a PDU SESSION ESTABLISHMENT REQUEST message (transported in UL NAS TRANSPORT with the PDU session ID); if accepted, the SMF creates a PDU SESSION ESTABLISHMENT ACCEPT message; if rejected, a PDU SESSION ESTABLISHMENT REJECT message with a 5GSM cause IE.

<details><summary>Excerpt TS 23.501 §5.6.1 — <code>23.501:5.6.1:1</code></summary>

> The matching of selected DNN to S-NSSAI is assumed to be based on network configuration.
> Each PDU Session supports a single PDU Session type i.e. supports the exchange of a single type of PDU requested by the UE at the establishment of the PDU Session. The following PDU Session types are defined: IPv4, IPv6, IPv4v6, Ethernet, Unstructured.
> PDU Sessions are established (upon UE request), modified (upon UE and 5GC request) and released (upon UE and 5GC request) using NAS SM signalling exchanged over N1 between the UE and the SMF. Upon request from an Application Server, the 5GC is able to trigger a specific application in the UE. When receiving that trigger message, the UE shall pass it to the identified application in the UE. The identified application in the UE may establish a PDU Session to a specific DNN, see clause 4.4.5.
> SMF may support PDU Sessions for LADN where the access to a DN 

</details>

<details><summary>Excerpt TS 24.501 §6.4.1 — <code>24.501:6.4.1.4.1:1</code></summary>

> the 5GSM cause value #28 "unknown PDU session type" in the 5GSM cause IE of the PDU SESSION ESTABLISHMENT REJECT message.
> If the PDU SESSION ESTABLISHMENT REQUEST message includes a PDU session type IE set to "Unstructured" or "Ethernet", and the subscription, the SMF configuration, or both, do not support the PDU session type for the requested DNN, the SMF shall include the 5GSM cause value #28 "unknown PDU session type" in the 5GSM cause IE of the PDU SESSION ESTABLISHMENT REJECT message.
> If the PDU SESSION ESTABLISHMENT REQUEST message is to establish an MA PDU session and includes a PDU session type IE set to "Unstructured", and the SMF configuration does not support the PDU session type, the SMF shall include the 5GSM cause value #28 "unknown PDU session type" in the 5GSM cause IE of the PDU SESSION ESTABLISHMENT REJECT message.
> If the PDU SESSION ESTABLISHMENT REQUEST message conta

</details>

## x-03 (cross) — NOT verified

**Q:** How does the UE indicate the network slices it wants during registration, and how is the NSSAI encoded in NAS?

- **TS 23.501** gold: §5.15.5.2, §5.15.2.1
- **TS 24.501** gold: §9.11.3.37, §5.5.1.2.2

**Reference answer:** TS 23.501: when registering with a PLMN, a UE with a Configured NSSAI and/or Allowed NSSAI provides, in AS and NAS layers, a Requested NSSAI containing the S-NSSAI(s) of the Network Slice(s) it wishes to register to; the Requested NSSAI lets the network select the serving AMF, network slices and instances. TS 24.501: the UE includes the S-NSSAIs in the Requested NSSAI IE of the REGISTRATION REQUEST message; the NSSAI information element identifies a collection of S-NSSAIs and is a type 4 IE with a minimum length of 4 octets and a maximum length of 146 octets.

<details><summary>Excerpt TS 23.501 §5.15.5.2 — <code>23.501:5.15.5.2.1:1</code></summary>

> rejected by the network (i.e. rejected in the current registration area or rejected in the PLMN). For the registration to a PLMN for which neither a Configured NSSAI applicable to this PLMN or an Allowed NSSAI are present, the S-NSSAIs provided in the Requested NSSAI correspond to the S-NSSAI(s) in the Default Configured NSSAI unless the UE has HPLMN S-NSSAI for established PDU Session(s) in which case the HPLMN S-NSSAI(s) shall be provided in the mapping of Requested NSSAI in the NAS Registration Request message, with no corresponding VPLMN S-NSSAI in the Requested NSSAI. If the UE has been provided with NSSRG information together with the Configured NSSAI, the UE only includes in the Requested NSSAI S-NSSAIs that share a common NSSRG, see clause 5.15.12.2. If the UE has stored Pending NSSAI and the UE is still interested in the Pending NSSAI then all the S-NSSAIs in the Requested NSSAI

</details>

<details><summary>Excerpt TS 23.501 §5.15.2.1 — <code>23.501:5.15.2.1:0</code></summary>

> Serving PLMN S-NSSAIs to HPLMN S-NSSAIs contains Serving PLMN S-NSSAI values and corresponding mapped HPLMN S-NSSAI values.
> The NSSAI is a collection of S-NSSAIs. An NSSAI may be a Configured NSSAI, a Requested NSSAI, Allowed NSSAI or a Partially Allowed NSSAI. There can be at most eight S-NSSAIs in Allowed NSSAI and Requested NSSAI sent in signalling messages between the UE and the Network. There can be at most seven S-NSSAIs in the Partially Allowed NSSAI and at most seven S-NSSAIs rejected partially in the RA and the sum of S-NSSAIs in the Allowed NSSAI and the Partially Allowed NSSAI shall be at most eight. The Requested NSSAI signalled by the UE to the network allows the network to select the Serving AMF, Network Slice(s) and Network Slice instance(s) for this UE, as specified in clause 5.15.5.
> NOTE 1: There can be at most a maximum of seven S-NSSAIs in the Partially Allowed NSSAI s

</details>

<details><summary>Excerpt TS 24.501 §9.11.3.37 — <code>24.501:9.11.3.37:1</code></summary>

> Figure: Figure 9.11.3.37.1: NSSAI information element]
> Table 9.11.3.37.1: NSSAI information element
> | Value part of the NSSAI information element (octet 3 to v) The value part of the NSSAI information element consists of one or more S-NSSAI values. Each S-NSSAI value consists of one S-NSSAI and optionally one mapped S-NSSAI. The recipient of this information element shall store the complete list received (NOTE 1, NOTE 2, NOTE 3). If the NSSAI information element conveys an allowed NSSAI and more than 8 S-NSSAI values are included in this information element, the UE shall store the first 8 S-NSSAI values and ignore the remaining octets of the information element. If the NSSAI information element conveys a configured NSSAI (including the default configured NSSAI) or pending NSSAI and more than 16 S-NSSAI values are included in this information element, the UE shall store the first 16 S-NSS

</details>

<details><summary>Excerpt TS 24.501 §5.5.1.2.2 — <code>24.501:5.5.1.2.2:4</code></summary>

> shall not include the S-NSSAI in the Requested NSSAI IE of the REGISTRATION REQUEST message for the current access type.
> If the UE has neither allowed NSSAI for the current PLMN or SNPN nor configured NSSAI for the current PLMN or SNPN and has a default configured NSSAI, the UE shall:
> - a) include the S-NSSAI(s) in the Requested NSSAI IE of the REGISTRATION REQUEST message using the default configured NSSAI; and
> - b) include the Network slicing indication IE with the Default configured NSSAI indication bit set to "Requested NSSAI created from default configured NSSAI" in the REGISTRATION REQUEST message.
> If the UE has no allowed NSSAI for the current PLMN or SNPN, no configured NSSAI for the current PLMN or SNPN, and no default configured NSSAI, the UE shall not include a requested NSSAI in the REGISTRATION REQUEST message.
> If all the S-NSSAI(s) corresponding to the slice(s) to which the

</details>

## x-04 (cross) — NOT verified

**Q:** What is the registration area and how does the periodic registration update timer work?

- **TS 23.501** gold: §5.3.2.3
- **TS 24.501** gold: §5.3.7, §10.2

**Reference answer:** TS 23.501: the registration area is the set of tracking areas in the TAI List that the AMF allocates to the UE when it registers over 3GPP access (managed per access type). TS 24.501: periodic registration update is used over 3GPP access to periodically notify the availability of the UE and is controlled by timer T3512 (default 54 min). When T3512 expires in 5GMM-IDLE mode the UE performs the periodic registration procedure (in 5GMM-CONNECTED mode it restarts T3512). The AMF keeps an implicit de-registration timer, by default 4 minutes greater than T3512; when it expires before the UE contacts the network, the network implicitly de-registers the UE.

<details><summary>Excerpt TS 23.501 §5.3.2.3 — <code>23.501:5.3.2.3:0</code></summary>

> Registration Area management comprises the functions to allocate and reallocate a Registration area to a UE. Registration area is managed per access type i.e. 3GPP access or Non-3GPP access.
> When a UE registers with the network over the 3GPP access, the AMF allocates a set of tracking areas in TAI List to the UE. When the AMF allocates registration area, i.e. the set of tracking areas in TAI List, to the UE it may take into account various information (e.g. Mobility Pattern and Allowed/Non-Allowed Area (refer to clause 5.3.4.1)). An AMF which has the whole PLMN as serving area may alternatively allocate the whole PLMN ("all PLMN") as registration area to a UE in MICO mode (refer to clause 5.4.1.3). When AMF allocates registration area for UE registered for Disaster Roaming service as specified in clause 5.40.4, AMF shall only consider TAIs covering the area with the Disaster Condition.
> T

</details>

<details><summary>Excerpt TS 24.501 §5.3.7 — <code>24.501:5.3.7:0</code></summary>

> The registration procedure for periodic registration update is used over 3GPP access to periodically notify the availability of the UE to the network. The procedure is controlled in the UE by the periodic registration update timer, T3512.
> If the UE is registered over the 3GPP access, the AMF maintains an implicit de-registration timer to control when the UE is considered implicitly de-registered over the 3GPP access. If the UE is registered over the non-3GPP access, the AMF also maintains a non-3GPP implicit de-registration timer to control when the UE is considered implicitly de-registered over the non-3GPP access. The UE registered over the non-3GPP access maintains a non-3GPP de-registration timer to control when the UE is considered implicitly de-registered for the non-3GPP access.
> The AMF shall start a non-3GPP implicit de-registration timer for the UE registered over non-3GPP acces

</details>

<details><summary>Excerpt TS 24.501 §10.2 — <code>24.501:10.2:9</code></summary>

> services, the value of this timer is set equal to the value of timer T3512. If the T3346 value provided in the mobility management messages is greater than the value of the timer T3512, the AMF sets the mobile reachable timer and the implicit de-registration timer such that the sum of the timer values is greater than the value of timer T3346. NOTE 2: The value of this timer is network dependent. If MICO is activated, the default value of this timer is 4 minutes greater than the value of timer T3512. NOTE 3: The value of this timer is network dependent. The default value of this timer is 4 minutes greater than the non-3GPP de-registration timer. If the T3346 value provided in the mobility management messages is greater than the value of the non-3GPP de-registration timer, the AMF sets the non-3GPP implicit de-registration timer value to be 8 minutes greater than the value of timer T3346. 

</details>

## x-05 (cross) — NOT verified

**Q:** How are user plane resources of existing PDU sessions re-activated with the service request procedure?

- **TS 23.501** gold: §5.6.8
- **TS 24.501** gold: §5.6.1

**Reference answer:** TS 23.501: activation of a UP connection of an existing PDU Session activates its UE-CN user plane connection (data radio bearer and N3 tunnel); for a UE in CM-IDLE in 3GPP access, the UE- or Network-Triggered Service Request procedure may support independent activation of UP connections of existing PDU Sessions. TS 24.501: one purpose of the service request procedure is to request the establishment of user-plane resources for PDU sessions established without user-plane resources, and to move the UE from 5GMM-IDLE to 5GMM-CONNECTED mode; the UE invokes it e.g. when it has uplink user data pending or receives a paging request.

<details><summary>Excerpt TS 23.501 §5.6.8 — <code>23.501:5.6.8:0</code></summary>

> This clause applies to the case when a UE has established multiple PDU Sessions. The activation of a UP connection of an existing PDU Session causes the activation of its UE-CN User Plane connection (i.e. data radio bearer and N3 tunnel).
> For the activation of a UP connection the service area restrictions as specified in clause 5.3.4.1.1 apply.
> For the UE in the CM-IDLE state in 3GPP access, either UE or Network-Triggered Service Request procedure may support independent activation of UP connection of existing PDU Session. For the UE in the CM-IDLE state in non-3GPP access, UE-Triggered Service Request procedure allows the re-activation of UP connection of existing PDU Sessions and may support independent activation of UP connection of existing PDU Session.
> A UE in the CM-CONNECTED state invokes a Service Request (see clause 4.2.3.2 of TS 23.502 [3]) procedure to request the independent 

</details>

<details><summary>Excerpt TS 24.501 §5.6.1 — <code>24.501:5.6.1.1:0</code></summary>

> 3GPP access and the UE is in 5GMM-IDLE mode over 3GPP access;
> - the network has downlink signalling pending over non-3GPP access, the UE is in 5GMM-IDLE mode over non-3GPP access and in 5GMM-IDLE or 5GMM-CONNECTED mode over 3GPP access;
> - the UE has uplink signalling pending over 3GPP access and the UE is in 5GMM-IDLE mode over 3GPP access;
> - the network has downlink user data pending over 3GPP access and the UE is in 5GMM-IDLE mode over 3GPP access;
> - the network has downlink user data pending over non-3GPP access, the UE is in 5GMM-IDLE mode over non-3GPP access and in 5GMM-IDLE or 5GMM-CONNECTED mode over 3GPP access;
> - the UE has user data pending over 3GPP access and the UE is in 5GMM-IDLE or 5GMM-CONNECTED mode over 3GPP access;
> - the UE has user data pending over non-3GPP access and the UE is in 5GMM-CONNECTED mode over non-3GPP access;
> - the UE in 5GMM-IDLE mode over non-3GPP acc

</details>

## x-06 (cross) — NOT verified

**Q:** How does a UE deregister from the 5G System, from the registration management states to the NAS messages used?

- **TS 23.501** gold: §5.3.2.2
- **TS 24.501** gold: §5.5.2

**Reference answer:** TS 23.501: two RM states are used in the UE and the AMF, RM-DEREGISTERED and RM-REGISTERED; in RM-REGISTERED the UE performs the Deregistration procedure and enters RM-DEREGISTERED when it no longer needs to be registered with the PLMN, and may deregister at any time. TS 24.501: the de-registration procedure is used by the UE or by the network, per access type; in the UE-initiated case the UE sends a DEREGISTRATION REQUEST message whose De-registration type IE indicates whether it is due to switch off, and enters 5GMM-DEREGISTERED-INITIATED.

<details><summary>Excerpt TS 23.501 §5.3.2.2 — <code>23.501:5.3.2.2.3:0</code></summary>

> re-negotiate protocol parameters with the network;
> - perform Deregistration procedure (see clause 4.2.2.3.1 of TS 23.502 [3]) and enter RM-DEREGISTERED state, when the UE needs to be no longer registered with the PLMN. The UE may decide to deregister from the network at any time.
> - enter RM-DEREGISTERED state when receiving a Registration Reject message or a Deregistration message. The actions of the UE depend upon the cause value' in the Registration Reject or Deregistration message. See clause 4.2.2 of TS 23.502 [3].
> When the UE RM state in the AMF is RM-REGISTERED, the AMF shall:
> - perform Deregistration procedure (see clauses 4.2.2.3.2, 4.2.2.3.3 of TS 23.502 [3]) and enter RM-DEREGISTERED state for the UE, when the UE needs to be no longer registered with the PLMN. The network may decide to deregister the UE at any time;
> - perform Implicit Deregistration at any time after the Implic

</details>

<details><summary>Excerpt TS 24.501 §5.5.2 — <code>24.501:5.5.2.2.6:1</code></summary>

> De-registration procedure collision.
> - De-registration containing de-registration type "switch off":
>   - If the UE receives a DEREGISTRATION REQUEST message before the UE-initiated de-registration procedure has been completed, this message shall be ignored and the UE-initiated de-registration procedure shall continue.
> - Otherwise:
>   - If the UE receives a DEREGISTRATION REQUEST message before the UE-initiated de-registration procedure has been completed, it shall treat the message as specified in clause 5.5.2.3.2 with the following modification:
>     - If the DEREGISTRATION REQUEST message received by the UE contains de-registration type "re-registration required", and the UE-initiated de-registration procedure is with de-registration type "normal de-registration":
>       - If the access type included in the DEREGISTRATION REQUEST message sent by the UE is same as access type sent by the n

</details>

## x-07 (cross) — NOT verified

**Q:** How are authentication and NAS security established between the UE and the AMF?

- **TS 23.501** gold: §5.10.1, §6.2.1
- **TS 24.501** gold: §5.4.1, §5.4.2

**Reference answer:** TS 23.501: 5GS security features include mutual authentication between UE and network, security context generation and distribution, and control plane signalling confidentiality and integrity protection; the AMF terminates NAS with NAS ciphering and integrity protection and includes access authentication and the Security Anchor Functionality (SEAF). TS 24.501: the primary authentication and key agreement procedure provides mutual authentication and keying material, with two methods (EAP based and 5G AKA based) that UE and AMF shall support; then the NAS security mode control procedure takes a 5G NAS security context into use and starts NAS signalling security between UE and AMF with the 5G NAS keys and algorithms (SECURITY MODE COMMAND / SECURITY MODE COMPLETE).

<details><summary>Excerpt TS 23.501 §5.10.1 — <code>23.501:5.10.1:0</code></summary>

> The security features in the 5G System include:
> - Authentication of the UE by the network and vice versa (mutual authentication between UE and network).
> - Security context generation and distribution.
> - User Plane data confidentiality and integrity protection.
> - Control Plane signalling confidentiality and integrity protection.
> - User identity confidentiality.
> - Support of LI requirements as specified in TS 33.126 [35] subject to regional/national regulatory requirements, including protection of LI data (e.g. target list) that may be stored or transferred by an NF.
> Detailed security related network functions for 5G are described in TS 33.501 [29].

</details>

<details><summary>Excerpt TS 23.501 §6.2.1 — <code>23.501:6.2.1:1</code></summary>

> Reports that are sent to the HPLMN.
> In addition to the functionality of the AMF described above, the AMF may provide support for Network Slice restriction and Network Slice instance restriction based on NWDAF analytics.
> In addition to the functionalities of the AMF described above, the AMF may provide support for the Disaster Roaming as described in clause 5.40.
> In addition to the functionalities of the AMF described above, the AMF may also include following functionalities to support Network Slice Admission Control:
> - Support of NSAC for maximum number of UEs as defined in clauses 5.15.11.1 and 5.15.11.3.
> In addition to the functionality of the AMF described above, the AMF may include the following functionality to support SNPNs:
> - Support for Onboarding of UEs for SNPNs.
> In addition to the functionalities of the AMF described above, the AMF may also include following functionalities to

</details>

<details><summary>Excerpt TS 24.501 §5.4.1 — <code>24.501:5.4.1.2.1:0</code></summary>

> the serving AMF intends to initiate a security mode control procedure after the EAP based primary authentication and key agreement procedure and the security mode control procedure intends to bring into use the partial native 5G NAS security context created by the EAP based primary authentication and key agreement procedure, then the EAP-success message and the ngKSI are transported from the network to the UE using the SECURITY MODE COMMAND message of the security mode control procedure (see clause 5.4.2).
> If the authentication of the UE completes successfully and the serving AMF does not intend to initiate a security mode control procedure bringing into use the partial native 5G NAS security context created by the EAP based primary authentication and key agreement procedure, then the EAP-success message, and the ngKSI are transported from the network to the UE using the AUTHENTICATION R

</details>

<details><summary>Excerpt TS 24.501 §5.4.2 — <code>24.501:5.4.2.2:2</code></summary>

> AMF includes the ngKSI in the SECURITY MODE COMMAND message over the 3GPP access. When the AMF sends the SECURITY MODE COMMAND message to UE over the non-3GPP access to take into use the new 5G NAS security context, the AMF shall include the same ngKSI in the SECURITY MODE COMMAND message to identify the new 5G NAS security context; or
> - b) the non-3GPP access, the AMF includes the ngKSI in the SECURITY MODE COMMAND message over the non-3GPP access. When the AMF sends the SECURITY MODE COMMAND message to UE over the 3GPP access to take into use the new 5G NAS security context, the AMF shall include the same ngKSI in the SECURITY MODE COMMAND message to identify the new 5G NAS security context.
> The AMF may initiate a SECURITY MODE COMMAND in order to change the 5G security algorithms for a current 5G NAS security context already in use. The AMF re-derives the 5G NAS keys from KAMF with th

</details>

## o-01 (out_of_corpus) — NOT verified

**Q:** What is the maximum PHY data rate of Wi-Fi 7 (IEEE 802.11be)?

Expected: refusal sentence. Corpus search for the topic found no match.

## o-02 (out_of_corpus) — NOT verified

**Q:** How does the GSM A5/1 stream cipher generate its keystream?

Expected: refusal sentence. Corpus search for the topic found no match.

## o-03 (out_of_corpus) — NOT verified

**Q:** How does OSPF compute the shortest path between routers in an area?

Expected: refusal sentence. Corpus search for the topic found no match.
