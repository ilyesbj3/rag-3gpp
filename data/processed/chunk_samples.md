# Chunk samples for human review

3597 chunks in `data/processed/chunks.jsonl`. Regenerate with `python scripts/sample_chunks.py --n 15 --seed 42`.

## Topic chunks (found by searching the chunk text)

**5GMM cause #9** — matching chunks: 24.501:A.1:0

### `24.501:A.1:0` — 5GMM cause #9

- spec: TS 24.501 18.14.0 (Rel-18) · section: **A.1** · title: Causes related to UE identification
- breadcrumb: A > A.1 · content_type: text · part: 0 · tokens: 290

````text
[TS 24.501 §A.1 Causes related to UE identification | A Cause values for 5GS mobility management]
Cause #3 – Illegal UE
- This 5GMM cause is sent to the UE when the network refuses service to the UE either because an identity of the UE is not acceptable to the network or because the UE does not pass the authentication check.
Cause #6 – Illegal ME
- This 5GMM cause is sent to the UE if the ME used is not acceptable to the network, e.g. on the prohibited list.
Cause #9 – UE identity cannot be derived by the network.
- This 5GMM cause is sent to the UE when the network cannot derive the UE's identity from the 5G-GUTI or 5G-S-TMSI because of e.g. no matching identity/context in the network, failure to validate the UE's identity due to integrity check failure of the received message.
Cause #10 – Implicitly de-registered
- This 5GMM cause is sent to the UE either if the network has implicitly de-registered the UE, e.g. after the implicit de-registration timer has expired, or if the 5GMM context data related to the subscription does not exist in the AMF e.g. because of a AMF restart, or because of a registration request for mobility or registration update is routed to a new AMF.
````

**Timer T3510** — matching chunks: 24.501:10.2:1

### `24.501:10.2:1` — Timer T3510

- spec: TS 24.501 18.14.0 (Rel-18) · section: **10.2** · title: Timers of 5GS mobility management
- breadcrumb: 10 > 10.2 · content_type: table · part: 1 · tokens: 678

````text
[TS 24.501 §10.2 Timers of 5GS mobility management | 10 List of system parameters]
Table 10.2.1: Timers of 5GS mobility management – UE side
| TIMER NUM. | TIMER VALUE | STATE | CAUSE OF START | NORMAL STOP | ON EXPIRY |
|---|---|---|---|---|---|
| T3502 | Default 12 min. NOTE 1 | 5GMM-DEREGISTERED 5GMM-REGISTERED | At registration failure and the attempt counter is equal to 5 | Transmission of REGISTRATION REQUEST message | Initiation of the registration procedure, if still required |
| T3510 | 15s NOTE 7 NOTE 8 In WB-N1/CE mode, 85s For access via a satellite NG-RAN cell, 27s NOTE 12 | 5GMM-REGISTERED-INITIATED | Transmission of REGISTRATION REQUEST message | REGISTRATION ACCEPT message received or REGISTRATION REJECT message received | Start T3511 or T3502 as specified in clause 5.5.1.2.7 if T3510 expired during registration procedure for initial registration. Start T3511 or T3502 as specified in clause 5.5.1.3.7 if T3510 expired during the registration procedure for mobility and periodic registration update |
| T3511 | 10s | 5GMM-DEREGISTERED.ATTEMPTING-REGISTRATION 5GMM-REGISTERED.ATTEMPTING-REGISTRATION-UPDATE 5GMM-REGISTERED.NORMAL-SERVICE or 5GMM-REGISTERED.NON-ALLOWED-SERVICE | At registration failure due to lower layer failure, T3510 timeout or registration rejected with other 5GMM cause values than those treated in clause 5.5.1.2.5 for initial registration or clause 5.5.1.3.5 for mobility and periodic registration | Transmission of REGISTRATION REQUEST message 5GMM-CONNECTED mode entered (NOTE 5) | Retransmission of the REGISTRATION REQUEST message, if still required |
| T3512 | Default 54 min NOTE 1 NOTE 2 | 5GMM-REGISTERED | In 5GMM-REGISTERED, when 5GMM-CONNECTED mode is left and if the NW does not indicate support for strictly periodic registration timer as specified in clause 5.3.7. If the network indicates support for strictly periodic registration timer, T3512 is started after the successful completion of registration update procedure. T3512 is restarted if it expires in 5GMM-CONNECTED mode as specified in clause 5.3.7. | When entering state 5GMM-DEREGISTERED When entering 5GMM-CONNECTED mode if the NW does not indicate support for strictly periodic registration timer as specified in clause 5.3.7. | In 5GMM-IDLE mode, Initiation of the periodic registration procedure if the UE is not registered for emergency services. In 5GMM-CONNECTED mode, restart the timer T3512. Locally deregister if the UE is registered for emergency services |
````

**REGISTRATION REQUEST message** — matching chunks: 24.501:8.2.6.1:1, 24.501:8.2.6.1:2, 24.501:8.2.6.1:3

### `24.501:8.2.6.1:1` — REGISTRATION REQUEST message

- spec: TS 24.501 18.14.0 (Rel-18) · section: **8.2.6.1** · title: Message definition
- breadcrumb: 8 > 8.2 > 8.2.6 > 8.2.6.1 · content_type: table · part: 1 · tokens: 756

````text
[TS 24.501 §8.2.6.1 Message definition | 8 Message functional definitions and contents > 8.2 5GS mobility management messages > 8.2.6 Registration request]
Table 8.2.6.1.1: REGISTRATION REQUEST message content
| IEI | Information Element | Type/Reference | Presence | Format | Length |
|---|---|---|---|---|---|
|  | Extended protocol discriminator | Extended Protocol discriminator 9.2 | M | V | 1 |
|  | Security header type | Security header type 9.3 | M | V | 1/2 |
|  | Spare half octet | Spare half octet 9.5 | M | V | 1/2 |
|  | Registration request message identity | Message type 9.7 | M | V | 1 |
|  | 5GS registration type | 5GS registration type 9.11.3.7 | M | V | 1/2 |
|  | ngKSI | NAS key set identifier 9.11.3.32 | M | V | 1/2 |
|  | 5GS mobile identity | 5GS mobile identity 9.11.3.4 | M | LV-E | 6-n |
| C- | Non-current native NAS key set identifier | NAS key set identifier 9.11.3.32 | O | TV | 1 |
| 10 | 5GMM capability | 5GMM capability 9.11.3.1 | O | TLV | 3-15 |
| 2E | UE security capability | UE security capability 9.11.3.54 | O | TLV | 4-10 |
| 2F | Requested NSSAI | NSSAI 9.11.3.37 | O | TLV | 4-74 |
| 52 | Last visited registered TAI | 5GS tracking area identity 9.11.3.8 | O | TV | 7 |
| 17 | S1 UE network capability | S1 UE network capability 9.11.3.48 | O | TLV | 4-15 |
| 40 | Uplink data status | Uplink data status 9.11.3.57 | O | TLV | 4-34 |
| 50 | PDU session status | PDU session status 9.11.3.44 | O | TLV | 4-34 |
| B- | MICO indication | MICO indication 9.11.3.31 | O | TV | 1 |
| 2B | UE status | UE status 9.11.3.56 | O | TLV | 3 |
| 77 | Additional GUTI | 5GS mobile identity 9.11.3.4 | O | TLV-E | 14 |
| 25 | Allowed PDU session status | Allowed PDU session status 9.11.3.13 | O | TLV | 4-34 |
| 18 | UE's usage setting | UE's usage setting 9.11.3.55 | O | TLV | 3 |
| 51 | Requested DRX parameters | 5GS DRX parameters 9.11.3.2A | O | TLV | 3 |
| 70 | EPS NAS message container | EPS NAS message container 9.11.3.24 | O | TLV-E | 4-n |
````

### `24.501:8.2.6.1:2` — REGISTRATION REQUEST message

- spec: TS 24.501 18.14.0 (Rel-18) · section: **8.2.6.1** · title: Message definition
- breadcrumb: 8 > 8.2 > 8.2.6 > 8.2.6.1 · content_type: table · part: 2 · tokens: 750

````text
[TS 24.501 §8.2.6.1 Message definition | 8 Message functional definitions and contents > 8.2 5GS mobility management messages > 8.2.6 Registration request]
Table 8.2.6.1.1: REGISTRATION REQUEST message content
| IEI | Information Element | Type/Reference | Presence | Format | Length |
|---|---|---|---|---|---|
| 74 | LADN indication | LADN indication 9.11.3.29 | O | TLV-E | 3-811 |
| 8- | Payload container type | Payload container type 9.11.3.40 | O | TV | 1 |
| 7B | Payload container | Payload container 9.11.3.39 | O | TLV-E | 4-65538 |
| 9- | Network slicing indication | Network slicing indication 9.11.3.36 | O | TV | 1 |
| 53 | 5GS update type | 5GS update type 9.11.3.9A | O | TLV | 3 |
| 41 | Mobile station classmark 2 | Mobile station classmark 2 9.11.3.31C | O | TLV | 5 |
| 42 | Supported codecs | Supported codec list 9.11.3.51A | O | TLV | 5-n |
| 71 | NAS message container | NAS message container 9.11.3.33 | O | TLV-E | 4-n |
| 60 | EPS bearer context status | EPS bearer context status 9.11.3.23A | O | TLV | 4 |
| 6E | Requested extended DRX parameters | Extended DRX parameters 9.11.3.26A | O | TLV | 3-4 |
| 6A | T3324 value | GPRS timer 3 9.11.2.5 | O | TLV | 3 |
| 67 | UE radio capability ID | UE radio capability ID 9.11.3.68 | O | TLV | 3-n |
| 35 | Requested mapped NSSAI | Mapped NSSAI 9.11.3.31B | O | TLV | 3-42 |
| 48 | Additional information requested | Additional information requested 9.11.3.12A | O | TLV | 3 |
| 1A | Requested WUS assistance information | WUS assistance information 9.11.3.71 | O | TLV | 3-n |
| A- | N5GC indication | N5GC indication 9.11.3.72 | O | TV | 1 |
| 30 | Requested NB-N1 mode DRX parameters | NB-N1 mode DRX parameters 9.11.3.73 | O | TLV | 3 |
| 29 | UE request type | UE request type 9.11.3.76 | O | TLV | 3 |
| 28 | Paging restriction | Paging restriction 9.11.3.77 | O | TLV | 3-35 |
| 72 | Service-level-AA container | Service-level-AA container 9.11.2.10 | O | TLV-E | 4-65538 |
| 32 | NID | NID 9.11.3.79 | O | TLV | 8 |
````

**Standardized 5QI table** — matching chunks: 23.501:5.7.4:1, 23.501:5.7.4:2, 23.501:5.7.4:3, 23.501:5.7.4:4

### `23.501:5.7.4:1` — Standardized 5QI table

- spec: TS 23.501 18.12.0 (Rel-18) · section: **5.7.4** · title: Standardized 5QI to QoS characteristics mapping
- breadcrumb: 5 > 5.7 > 5.7.4 · content_type: table · part: 1 · tokens: 776

````text
[TS 23.501 §5.7.4 Standardized 5QI to QoS characteristics mapping | 5 High level features > 5.7 QoS model]
Table 5.7.4-1: Standardized 5QI to QoS characteristics mapping
| 5QI Value | Resource Type | Default Priority Level | Packet Delay Budget (NOTE 3) | Packet Error Rate | Default Maximum Data Burst Volume (NOTE 2) | Default Averaging Window | Example Services |
|---|---|---|---|---|---|---|---|
| 1 | GBR | 20 | 100 ms (NOTE 11, NOTE 13) | 10-2 | N/A | 2000 ms | Conversational Voice |
| 2 | (NOTE 1) | 40 | 150 ms (NOTE 11, NOTE 13) | 10-3 | N/A | 2000 ms | Conversational Video (Live Streaming) |
| 3 |  | 30 | 50 ms (NOTE 11, NOTE 13) | 10-3 | N/A | 2000 ms | Real Time Gaming, V2X messages (see TS 23.287 [121]). Electricity distribution – medium voltage, Process automation monitoring |
| 4 |  | 50 | 300 ms (NOTE 11, NOTE 13) | 10-6 | N/A | 2000 ms | Non-Conversational Video (Buffered Streaming) |
| 65 (NOTE 9, NOTE 12) |  | 7 | 75 ms (NOTE 7, NOTE 8) | 10-2 | N/A | 2000 ms | Mission Critical user plane Push To Talk voice (e.g. MCPTT) |
| 66 (NOTE 12) |  | 20 | 100 ms (NOTE 10, NOTE 13) | 10-2 | N/A | 2000 ms | Non-Mission-Critical user plane Push To Talk voice |
| 67 (NOTE 12) |  | 15 | 100 ms (NOTE 10, NOTE 13) | 10-3 | N/A | 2000 ms | Mission Critical Video user plane |
| 75 (NOTE 14) |  | 25 | 50 ms (NOTE 13) | 10-2 | N/A | 2000 ms | V2X messages (see TS 23.287 [121]). A2X messages (see TS 23.256 [136]) |
| 71 |  | 56 | 150 ms (NOTE 11, NOTE 13, NOTE 15) | 10-6 | N/A | 2000 ms | "Live" Uplink Streaming (e.g. TS 26.238 [76]) |
| 72 |  | 56 | 300 ms (NOTE 11, NOTE 13, NOTE 15) | 10-4 | N/A | 2000 ms | "Live" Uplink Streaming (e.g. TS 26.238 [76]) |
| 73 |  | 56 | 300 ms (NOTE 11, NOTE 13, NOTE 15) | 10-8 | N/A | 2000 ms | "Live" Uplink Streaming (e.g. TS 26.238 [76]) |
| 74 |  | 56 | 500 ms (NOTE 11, NOTE 15) | 10-8 | N/A | 2000 ms | "Live" Uplink Streaming (e.g. TS 26.238 [76]) |
````

### `23.501:5.7.4:2` — Standardized 5QI table

- spec: TS 23.501 18.12.0 (Rel-18) · section: **5.7.4** · title: Standardized 5QI to QoS characteristics mapping
- breadcrumb: 5 > 5.7 > 5.7.4 · content_type: table · part: 2 · tokens: 772

````text
[TS 23.501 §5.7.4 Standardized 5QI to QoS characteristics mapping | 5 High level features > 5.7 QoS model]
Table 5.7.4-1: Standardized 5QI to QoS characteristics mapping
| 5QI Value | Resource Type | Default Priority Level | Packet Delay Budget (NOTE 3) | Packet Error Rate | Default Maximum Data Burst Volume (NOTE 2) | Default Averaging Window | Example Services |
|---|---|---|---|---|---|---|---|
| 76 |  | 56 | 500 ms (NOTE 11, NOTE 13, NOTE 15) | 10-4 | N/A | 2000 ms | "Live" Uplink Streaming (e.g. TS 26.238 [76]) |
| 5 | Non-GBR | 10 | 100 ms (NOTE 10, NOTE 13) | 10-6 | N/A | N/A | IMS Signalling |
| 6 | (NOTE 1) | 60 | 300 ms (NOTE 10, NOTE 13) | 10-6 | N/A | N/A | Video (Buffered Streaming) TCP-based (e.g. www, e-mail, chat, ftp, p2p file sharing, progressive video, etc.), AI/ML model download for image recognition (e.g. for model topology) (see TS 22.261 [2]) |
| 7 |  | 70 | 100 ms (NOTE 10, NOTE 13) | 10-3 | N/A | N/A | Voice, Video (Live Streaming) Interactive Gaming, AI/ML model download for image recognition (e.g. for model weight factors) (see TS 22.261 [2]) |
| 8 |  | 80 | 300 ms (NOTE 10, NOTE 13) | 10-6 | N/A | N/A | Video (Buffered Streaming) TCP-based (e.g. www, e-mail, chat, ftp, p2p file sharing, progressive |
| 9 |  | 90 |  |  |  |  | video, etc.) |
| 10 |  | 90 | 1100ms (NOTE 10,NOTE 13, NOTE 17) | 10-6 | N/A | N/A | Video (Buffered Streaming) TCP-based (e.g. www, e-mail, chat, ftp, p2p file sharing, progressive video, etc.) and any service that can be used over satellite access type with these characteristics |
| 69 (NOTE 9, NOTE 12) |  | 5 | 60 ms (NOTE 7, NOTE 8) | 10-6 | N/A | N/A | Mission Critical delay sensitive signalling (e.g. MC-PTT signalling) |
| 70 (NOTE 12) |  | 55 | 200 ms (NOTE 7, NOTE 10) | 10-6 | N/A | N/A | Mission Critical Data (e.g. example services are the same as 5QI 6/8/9) |
| 79 |  | 65 | 50 ms (NOTE 10, NOTE 13) | 10-2 | N/A | N/A | V2X messages (see TS 23.287 [121]) |
| 80 |  | 68 | 10 ms (NOTE 5, NOTE 10) | 10-6 | N/A | N/A | Low Latency eMBB applications Augmented Reality |
````

## Random chunks

### `24.501:8.2.6.12:0` — random

- spec: TS 24.501 18.14.0 (Rel-18) · section: **8.2.6.12** · title: Additional GUTI
- breadcrumb: 8 > 8.2 > 8.2.6 > 8.2.6.12 · content_type: text · part: 0 · tokens: 141

````text
[TS 24.501 §8.2.6.12 Additional GUTI | 8 Message functional definitions and contents > 8.2 5GS mobility management messages > 8.2.6 Registration request]
This IE shall be included:
- a) if the UE performs the registration procedure due to inter-system change from S1 mode to N1 mode, the UE operates in single-registration mode and the UE has a valid 5G-GUTI; or
- b) the UE holds two valid native 5G-GUTIs and one of the valid native 5G-GUTI was assigned by the PLMN with which the UE is performing the registration.
````

### `23.501:5.15.6:0` — random

- spec: TS 23.501 18.12.0 (Rel-18) · section: **5.15.6** · title: Network Slicing Support for Roaming
- breadcrumb: 5 > 5.15 > 5.15.6 · content_type: text · part: 0 · tokens: 702

````text
[TS 23.501 §5.15.6 Network Slicing Support for Roaming | 5 High level features > 5.15 Network slicing]
For roaming scenarios:
- If the UE only uses standard S-NSSAI values, then the same S-NSSAI values can be used in VPLMN as in the HPLMN.
- If the VPLMN and HPLMN have an SLA to support non-standard S-NSSAI values in the VPLMN, the NSSF of the VPLMN maps the Subscribed S-NSSAIs values to the respective S-NSSAI values to be used in the VPLMN. The S-NSSAI values to be used in the VPLMN are determined by the NSSF of the VPLMN based on the SLA. The NSSF of the VPLMN need not inform the HPLMN of which values are used in the VPLMN.
- Depending on operator's policy and the configuration in the AMF, the AMF may decide the S-NSSAI values to be used in the VPLMN and the mapping to the Subscribed S-NSSAIs.
- For the home routed case, the AMF or NSSF may select an S-NSSAI (if the UE does not provide an S-NSSAI for the PDU session establishment) and a Network Slice instance, based on load level and/or Observe Service Experience and/or Dispersion analytics of the VPLMN and/or that of the HPLMN from NWDAF as described in TS 23.288 [86].
- The UE constructs Requested NSSAI and provides the mapping of S-NSSAIs of the Requested NSSAI to HPLMN S-NSSAIs if the mapping is stored in the UE, as described in clause 5.15.5.2.1.
- The NSSF in the VPLMN determines the Allowed NSSAI without interacting with the HPLMN.
- the HPLMN may provide NSSRG Information as part of the Subscription information as described in clause 5.15.12.
- The Allowed NSSAI in the Registration Accept includes S-NSSAI values used in the VPLMN. The mapping information described above is also provided to the UE with the Allowed NSSAI as described in clause 5.15.4.
- If the S-NSSAI values are subject to NSAC, depending on operator's policy, a roaming agreement or an SLA between VPLMN and HPLMN, the AMF or SMF in VPLMN triggers a request for NSAC for these S-NSSAI values as described in clause 5.15.11.3.
- In PDU Session Establishment procedure, the UE includes both:
  - (a) the S-NSSAI that matches the application (that is triggering the PDU Session Request) within the NSSP in the URSP rules or within the UE Local Configuration as defined in clause 6.1.2.2.1 of TS 23.503 [45]; the value of this S NSSAI is used in the HPLMN; and
  - (b) an S-NSSAI belonging to the Allowed NSSAI that maps to (a) using the mapping of the Allowed NSSAI to HPLMN S-NSSAIs; the value of this S-NSSAI is used in the VPLMN.
````

### `23.501:5.3.2.3:0` — random

- spec: TS 23.501 18.12.0 (Rel-18) · section: **5.3.2.3** · title: Registration Area management
- breadcrumb: 5 > 5.3 > 5.3.2 > 5.3.2.3 · content_type: text · part: 0 · tokens: 787

````text
[TS 23.501 §5.3.2.3 Registration Area management | 5 High level features > 5.3 Registration and Connection Management > 5.3.2 Registration Management]
Registration Area management comprises the functions to allocate and reallocate a Registration area to a UE. Registration area is managed per access type i.e. 3GPP access or Non-3GPP access.
When a UE registers with the network over the 3GPP access, the AMF allocates a set of tracking areas in TAI List to the UE. When the AMF allocates registration area, i.e. the set of tracking areas in TAI List, to the UE it may take into account various information (e.g. Mobility Pattern and Allowed/Non-Allowed Area (refer to clause 5.3.4.1)). An AMF which has the whole PLMN as serving area may alternatively allocate the whole PLMN ("all PLMN") as registration area to a UE in MICO mode (refer to clause 5.4.1.3). When AMF allocates registration area for UE registered for Disaster Roaming service as specified in clause 5.40.4, AMF shall only consider TAIs covering the area with the Disaster Condition.
The 5G System shall support allocating a Registration Area using a single TAI List which includes tracking areas of any NG-RAN nodes in the Registration Area for a UE.
In the case of SNPN, the TAI list allocated by AMF does not support Tracking Areas belonging to different SNPNs.
TAI used for non-3GPP access shall be dedicated to non-3GPP access. TAI(s) dedicated to Non-3GPP access may be defined in a PLMN and apply within this PLMN. Each N3IWF, TNGF, TWIF and W-AGF is locally configured with one TAI value. Each N3IWF, TNGF, TWIF and W-AGF may be configured with a different TAI value or with the same TAI value as other N3IWFs, TNGFs, TWIFs and/or W-AGFs. The TAI is provided to the AMF during N2 interface setup and as part of the User Location Information in UE associated messages as described in TS 38.413 [34].
When a UE registers with the network over a Non-3GPP access, the AMF allocates to the UE a registration area that only includes the TAI received from the serving N3IWF, TNGF, TWIF or W-AGF.
NOTE 1: For example, two W-AGFs can each correspond to a different TAI (one TAI per W-AGF) and thus support different sets of S-NSSAI(s).
When generating the TAI list, the AMF shall include only TAIs that are applicable on the access type (i.e. 3GPP access or Non-3GPP access) where the TAI list is sent.
NOTE 2: To prevent extra signalling load resulting from Mobility Registration Update occurring at every RAT change, it is preferable to avoid generating a RAT-specific TAI list for a UE supporting more than one RAT.
NOTE 3: For a UE registered on N3GPP access the TAI(s) provided to the UE as part of the Registration Area is expected to enable the support of the slices that are intended to be provided for this UE over this specific Non-3GPP access. In addition, the Registration Area provided to the UE for non-3GPP access will never change until the UE deregisters from non-3GPP access (either explicit deregistration or implicit deregistration due to Deregistration timer expiring due to UE entering CM_IDLE state).
````

### `24.501:9.10:0` — random

- spec: TS 24.501 18.14.0 (Rel-18) · section: **9.10** · title: Sequence number
- breadcrumb: 9 > 9.10 · content_type: text · part: 0 · tokens: 120

````text
[TS 24.501 §9.10 Sequence number | 9 General message format and information elements coding]
This IE includes the NAS message sequence number (SN) which consists of the eight least significant bits of the NAS COUNT for a SECURITY PROTECTED 5GS NAS MESSAGE message.
The NAS message sequence number (SN) with the eight least significant bits of the NAS COUNT is also included in the Intra N1 mode NAS transparent container IE and in the N1 mode to S1 mode NAS transparent container IE.
The usage of SN is specified in clause 4.4.3.
````

### `23.501:6.3.17:0` — random

- spec: TS 23.501 18.12.0 (Rel-18) · section: **6.3.17** · title: NSSAAF discovery and selection
- breadcrumb: 6 > 6.3 > 6.3.17 · content_type: text · part: 0 · tokens: 435

````text
[TS 23.501 §6.3.17 NSSAAF discovery and selection | 6 Network Functions > 6.3 Principles for Network Function and Network Function Service discovery and selection]
In the case of NF consumer based discovery and selection, the following applies:
- The NF consumer (e.g. AMF, AUSF) performs NSSAAF selection to select an NSSAAF Instance that supports authentication between the UE and the AAA-S associated with the HPLMN or in the Credentials Holder in the case of SNPN or in the DCS domain in the case of ON-SNPN. The NF consumer shall utilize the NRF to discover the NSSAAF instance(s) unless NSSAAF information is available by other means, e.g. locally configured on the NF consumer. The NSSAAF selection function in the NF consumer selects an NSSAAF instance based on the available NSSAAF instances (obtained from the NRF or locally configured in the NF consumer).
NSSAAF selection is applicable to both 3GPP access and non-3GPP access.
The NSSAAF selection function in NSSAAF NF consumers or in SCP should consider the following factor when it is available:
- 1. Home Network Identifier (e.g. MNC and MCC, realm) of SUPI (by an NF consumer in the Serving network).
- 2. S-NSSAI of the HPLMN.
- 3. SUPI or Internal Group ID; the NSSAAF NF consumer selects a NSSAAF instance based on the SUPI range the UE's SUPI belongs to or based on the results of a discovery procedure with NRF using the UE's SUPI or Internal Group ID as input for NSSAAF discovery.
An HPLMN deploying NSSAAF instances supporting specific S-NSSAIs and/or sets of SUPIs (according to factors 2-3) shall also deploy NSSAAF instance(s) that can be selected using factor 1 if they need to interoperate with VPLMNs using only factor 1 for NSSAAF selection.
In the case of delegated discovery and selection in SCP, the NSSAAF NF consumer shall send all available factors to the SCP.
````

### `23.501:5.45.3:0` — random

- spec: TS 23.501 18.12.0 (Rel-18) · section: **5.45.3** · title: Congestion information monitoring
- breadcrumb: 5 > 5.45 > 5.45.3 · content_type: text · part: 0 · tokens: 423

````text
[TS 23.501 §5.45.3 Congestion information monitoring | 5 High level features > 5.45 QoS Monitoring]
The NG-RAN may be required to provide the UL and/or DL QoS Flow congestion information to UPF (i.e. a percentage of congestion level for exposure). The UPF may be required to monitor and expose the UL and/or DL QoS Flow congestion information reported from the NG-RAN.
QoS monitoring request for congestion information provided by the SMF to the NG-RAN is to trigger the NG-RAN to measure and report UL and/or DL QoS Flow congestion information to PSA UPF as defined in 5.37.3.
NOTE 1: How the RAN measures and reports the congestion information is up to RAN implementation.
NOTE 2: It is assumed that the RAN reports whenever there is a change in the percentage of packets to be marked with ECN for L4S marking and/or congestion information. The granularity of change in percentage determination is up to RAN implementation.
For the reporting of the congestion information from PSA UPF, the periodical reporting is not applied and only the Reporting frequency 'event triggered' applies, see clause 5.8.2.18.
The PSA UPF reports the received UL and/or DL QoS Flow congestion information to the target NF as instructed by the QoS Monitoring request (see clause 5.8.2.18) from the SMF.
Only ECN marking for L4S in NG-RAN (as described in clause 5.37.3) or QoS monitoring of congestion information may be requested to NG-RAN for a QoS Flow. QoS Monitoring of congestion information for exposure and ECN marking for L4S (in NG-RAN or UPF) are mutually exclusive, therefore, measurements of Congestion information on a QoS Flow are not exposed in QoS Monitoring reports if SMF enables ECN marking for L4S (see clauses 5.37.3 and 5.37.4).
````

### `23.501:5.33.3.3:1` — random

- spec: TS 23.501 18.12.0 (Rel-18) · section: **5.33.3.3** · title: GTP-U Path Measurement
- breadcrumb: 5 > 5.33 > 5.33.3 > 5.33.3.3 · content_type: text · part: 1 · tokens: 458

````text
[TS 23.501 §5.33.3.3 GTP-U Path Measurement | 5 High level features > 5.33 Support for Ultra Reliable Low Latency Communication > 5.33.3 QoS Monitoring for packet delay]
- RAN measures and provides the RAN part of UL/DL packet delay towards UPF (in the GTP-U header of the respective QoS Flow via N3).
- The UPF calculates the UL/DL packet delay by combining the received measurements of RAN part with the measurements of N3/N9 interface (N9 is applicable when I-UPF exists).
- The UPF reports the QoS Monitoring results as described in clause 5.8.2.18.
QoS Monitoring can also be used to measure the packet delay for transport paths to influence the mapping of QoS Flows to appropriate network instances, DSCP values as follows:
- SMF activates QoS monitoring for the GTP-U path(s) between all UPF(s) and all (R)AN nodes based on locally configured policies.
- UPF does measurement of network hop delay per transport resources that it will use towards a peer network node identified by an IP destination address (the hop between these two nodes) and port. The network hop measured delay is computed by sending an Echo Request over such transport resource (Ti) and measuring RTT/2 when Echo Response is received.
- UPF maps {network instance, DSCP} into Transport Resource and measures delay per IP destination address and port. Thus, for each IP destination address, the measured delay per (network instance, DSCP) entry is determined.
- The UPF performing the QoS monitoring can provide the corresponding {Network instance, DSCP} along with the measured accumulated packet delay for the corresponding transport path to the SMF. The UPF reports the measurement results to the SMF based on some specific conditions e.g. first time, periodic, event triggered, when thresholds for reporting towards SMF (via N4) are reached.
- Based on this, SMF can determine QoS Flow mapping to the appropriate {Network instance, DSCP} considering {5QI, QoS characteristics, ARP} for the given QoS Flow.
````

### `23.501:5.17.2.1:6` — random

- spec: TS 23.501 18.12.0 (Rel-18) · section: **5.17.2.1** · title: General
- breadcrumb: 5 > 5.17 > 5.17.2 > 5.17.2.1 · content_type: text · part: 6 · tokens: 309

````text
[TS 23.501 §5.17.2.1 General | 5 High level features > 5.17 Interworking and Migration > 5.17.2 Interworking with EPC]
If a Service Gap timer is running in the MME when the UE moves from EPC to 5GC, the MME stops the running Service Gap timer. If the UE returns to E-UTRAN connected to EPC from 5GC the MME provides the Service Gap Time to the UE as described in TS 23.401 [26].
If a Service Gap timer is running in the UE when the UE moves to from 5GC to EPC and if Service Gap Time is received from the MME, the UE stores the received Service Gap Time for later use when the timer needs to be started next time and the Service Gap timer that was started before the system change is kept running in the UE and applied for EPC. If a Service Gap timer is running in the UE when the UE moves to 5GC and if Service Gap Time is received from the AMF, the UE stores the received Service Gap Time for later use when the timer needs to be started next time and the Service Gap timer that was started before the system change is kept running in the UE and applied in 5GS.
For UE currently served by EPC, a SMF+PGW-C may support L2TP tunnelling on N6, as described in clause 5.8.2.16.
````

### `24.501:8.3.16.1:0` — random

- spec: TS 24.501 18.14.0 (Rel-18) · section: **8.3.16.1** · title: Message definition
- breadcrumb: 8 > 8.3 > 8.3.16 > 8.3.16.1 · content_type: text · part: 0 · tokens: 288

````text
[TS 24.501 §8.3.16.1 Message definition | 8 Message functional definitions and contents > 8.3 5GS session management messages > 8.3.16 5GSM status]
The 5GSM STATUS message is sent by the SMF or the UE to pass information on the status of the indicated PDU session and report certain error conditions. See table 8.3.16.1.1.
- Message type: 5GSM STATUS
- Significance: dual
- Direction: both
Table 8.3.16.1.1: 5GSM STATUS message content
| IEI | Information Element | Type/Reference | Presence | Format | Length |
|---|---|---|---|---|---|
|  | Extended protocol discriminator | Extended protocol discriminator 9.2 | M | V | 1 |
|  | PDU session ID | PDU session identity 9.4 | M | V | 1 |
|  | PTI | Procedure transaction identity 9.6 | M | V | 1 |
|  | 5GSM STATUS message identity | Message type 9.7 | M | V | 1 |
|  | 5GSM cause | 5GSM cause 9.11.4.2 | M | V | 1 |
````

### `23.501:5.13:1` — random

- spec: TS 23.501 18.12.0 (Rel-18) · section: **5.13** · title: Support for Edge Computing
- breadcrumb: 5 > 5.13 · content_type: text · part: 1 · tokens: 348

````text
[TS 23.501 §5.13 Support for Edge Computing | 5 High level features]
- QoS and Charging: PCF provides rules for QoS Control and Charging for the traffic routed to the local part of the DN;
- Support of Local Area Data Network: 5G Core Network provides support to connect to the LADN in a certain area where the applications are deployed as described in clause 5.6.5.
- Discovery and re-discovery of Edge Applications Servers as described in TS 23.548 [130].
- Support of Edge Relocation as described in TS 23.548 [130] and the case of involving AF change as described in clauses 4.3.6.2, 4.3.6.3 and 4.3.6.4 of TS 23.502 [3]. Support of 5GC triggered Edge relocation within the same hosting PLMN's EHEs.
- Support of (I-)SMF (re)selection based on DNAI as described in clauses 4.3.5.1, 4.3.5.2 and 4.23.5.1 of TS 23.502 [3].
- Support of finer sets of UEs.
- Support of common EAS discovery and common DNAI determination for set of UEs as described in clause 6.2 of TS 23.548 [130].
- Support of mapping information between EAS IP/IP range and DNAI as described in clause 6.8 of TS 23.548 [130].
- Support of AF request for DNAI as described in clause 6.8 of TS 23.548 [130].
````

### `24.501:8.2.14.10:0` — random

- spec: TS 24.501 18.14.0 (Rel-18) · section: **8.2.14.10** · title: Forbidden TAI(s) for the list of "5GS forbidden tracking areas for regional provision of service"
- breadcrumb: 8 > 8.2 > 8.2.14 > 8.2.14.10 · content_type: text · part: 0 · tokens: 118

````text
[TS 24.501 §8.2.14.10 Forbidden TAI(s) for the list of "5GS forbidden tracking areas for regional provision of service" | 8 Message functional definitions and contents > 8.2 5GS mobility management messages > 8.2.14 De-registration request (UE terminated de-registration)]
This IE is included to indicate the forbidden TAI(s) to be stored in the list of "5GS forbidden tracking areas for regional provision of service". This IE is included only if the message is sent via satellite NG-RAN access.
````

### `24.501:9.7:2` — random

- spec: TS 24.501 18.14.0 (Rel-18) · section: **9.7** · title: Message type
- breadcrumb: 9 > 9.7 · content_type: table · part: 2 · tokens: 604

````text
[TS 24.501 §9.7 Message type | 9 General message format and information elements coding]
Table 9.7.1: Message types for 5GS mobility management
| Bits | Bits | Bits | Bits | Bits | Bits | Bits | Bits |  |  |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 0 | 1 | 1 | 0 | 0 | 1 |  | Authentication failure |
| 0 | 1 | 0 | 1 | 1 | 0 | 1 | 0 |  | Authentication result |
| 0 | 1 | 0 | 1 | 1 | 0 | 1 | 1 |  | Identity request |
| 0 | 1 | 0 | 1 | 1 | 1 | 0 | 0 |  | Identity response |
| 0 | 1 | 0 | 1 | 1 | 1 | 0 | 1 |  | Security mode command |
| 0 | 1 | 0 | 1 | 1 | 1 | 1 | 0 |  | Security mode complete |
| 0 | 1 | 0 | 1 | 1 | 1 | 1 | 1 |  | Security mode reject |
| 0 | 1 | 1 | 0 | 0 | 1 | 0 | 0 |  | 5GMM status |
| 0 | 1 | 1 | 0 | 0 | 1 | 0 | 1 |  | Notification |
| 0 | 1 | 1 | 0 | 0 | 1 | 1 | 0 |  | Notification response |
| 0 | 1 | 1 | 0 | 0 | 1 | 1 | 1 |  | UL NAS transport |
| 0 | 1 | 1 | 0 | 1 | 0 | 0 | 0 |  | DL NAS transport |
| 0 | 1 | 1 | 0 | 1 | 0 | 0 | 1 |  | Relay key request |
| 0 | 1 | 1 | 0 | 1 | 0 | 1 | 0 |  | Relay key accept |
| 0 | 1 | 1 | 0 | 1 | 0 | 1 | 1 |  | Relay key reject |
| 0 | 1 | 1 | 0 | 1 | 1 | 0 | 0 |  | Relay authentication request |
| 0 | 1 | 1 | 0 | 1 | 1 | 0 | 1 |  | Relay authentication response |
````

### `24.501:6.1.4.1:9` — random

- spec: TS 24.501 18.14.0 (Rel-18) · section: **6.1.4.1** · title: Coordination between 5GSM and ESM with N26 interface
- breadcrumb: 6 > 6.1 > 6.1.4 > 6.1.4.1 · content_type: text · part: 9 · tokens: 743

````text
[TS 24.501 §6.1.4.1 Coordination between 5GSM and ESM with N26 interface | 6 Elementary procedures for 5GS session management > 6.1 Overview > 6.1.4 Coordination between 5GSM and ESM]
    - B) flow description operation is "Delete existing QoS flow description", and the UE determines, by using the QoS rule's QFI as the 5QI, that there is a resulting QoS rule for a GBR QoS flow (as described in 3GPP TS 23.501 [8] table 5.7.4-1) with a QFI corresponding to the QFI of the QoS flow description that is deleted (i.e. there is no associated QoS flow description with the same QFI).
  - 7) When the flow description operation is "Create new QoS flow description" or "Modify existing QoS flow description", and the UE determines that there is a QoS flow description of a GBR QoS flow (as described in 3GPP TS 23.501 [8] table 5.7.4-1) which lacks at least one of the mandatory parameters (i.e. GFBR uplink, GFBR downlink, MFBR uplink and MFBR downlink). If the QoS flow description does not include a 5QI, the UE determines this by using the QFI as the 5QI.
  - 8) When the rule operation is "Create new QoS rule", "Modify existing QoS rule and add packet filters" or "Modify existing QoS rule and replace all packet filters" with a non-empty packet filter list in the QoS rule, and the DQR bit is set to "the QoS rule is the default QoS rule", the QoS rule is provided for a PDN connection of PDN type "non-IP" and there is locally available information associated with the PDN connection that is set to "Unstructured".
- In case 3 the UE shall not diagnose an error, further process the deletion request and, if no error according to items c and d was detected, consider the respective packet filter as successfully deleted.
- Otherwise the UE shall include a Protocol configuration options IE or Extended protocol configuration options IE with a 5GSM cause parameter set to 5GSM cause #84 "syntactical error in the QoS operation" in the MODIFY EPS BEARER CONTEXT ACCEPT message.
NOTE 3: It is not considered an error if the UE determines that after processing all QoS operations on QoS rules and QoS flow descriptions there is a QoS flow description that is not associated with any QoS rule and the UE is not in NB-N1 mode.
NOTE 3a: An implementation that strictly follows QoS rule operation as defined in clause 9.11.4.13 might not detect case 2).
- c) Semantic errors in packet filters:
  - 1) When a packet filter consists of conflicting packet filter components which would render the packet filter ineffective, i.e. no IP packet will ever fit this packet filter. How the UE determines a semantic error in a packet filter is outside the scope of the present document.
- The UE shall include a Protocol configuration options IE or Extended protocol configuration options IE with a 5GSM cause parameter set to 5GSM cause #44 "semantic errors in packet filter(s)" in the MODIFY EPS BEARER CONTEXT ACCEPT message.
- d) Syntactical errors in packet filters:
````

### `23.501:5.8.2.13.1:0` — random

- spec: TS 23.501 18.12.0 (Rel-18) · section: **5.8.2.13.1** · title: Support for unicast traffic forwarding of a 5G VN
- breadcrumb: 5 > 5.8 > 5.8.2 > 5.8.2.13 > 5.8.2.13.1 · content_type: text · part: 0 · tokens: 744

````text
[TS 23.501 §5.8.2.13.1 Support for unicast traffic forwarding of a 5G VN | 5 High level features > 5.8 User Plane Management > 5.8.2 Functional Description > 5.8.2.13 Support for 5G VN group communication]
To enable unicast traffic forwarding in a UPF, the following applies:
- The SMF provides for each 5G VN group member's N4 Session (i.e. N4 Session corresponding to PDU Session) the following N4 rules that enable the processing of packets received from this UE.
  - in order to detect the traffic, a PDR containing Source Interface set to "access side" and CN Tunnel Information set to PDU Session tunnel header (i.e. N3 or N9 GTP-U F-TEID); and
  - in order to forward the traffic, a FAR containing Destination Interface set to "5G VN internal".
- The SMF provides for each 5G VN group member's N4 Session (i.e. N4 session corresponding to PDU Session) the following N4 rules that enable the processing of packets towards this UE.
  - in order to detect the traffic, a PDR containing Source Interface set to "5G VN internal" and Destination Address set to the IP/MAC address (es) of this 5G VN group member; and
  - in order to forward the traffic, a FAR containing Outer Header Creation indicating the N3/N9 tunnel information and Destination Interface set "access side".
- If N19-based forwarding is applied, the SMF configures the group-level N4 Session for processing packets received from a N19 tunnel with the following N4 rules for each N19 tunnel.
  - in order to detect the traffic, a PDR containing Source Interface set to "core side" and CN Tunnel Information set to N19 tunnel header (i.e. N19 GTP-U F-TEID); and
  - in order to forward the traffic, a FAR containing Destination Interface set to "5G VN internal".
- If N19-based forwarding is applied, the SMF configures the group-level N4 Session for processing packets towards 5G VN group members anchored at other UPFs with the following N4 rules for each N19 tunnel.
  - in order to detect the traffic, a PDR containing Source Interface set to "5G VN internal" and Destination Address set to the IP/MAC address (es) of UEs anchored at the peer UPF of this N19 tunnel (e.g. based on the IP address range supported by the peer UPF); and
  - in order to forward the traffic to a 5G VN group member anchored at another UPF via the N19 tunnel, a FAR containing Outer Header Creation indicating the N19 tunnel information, Destination Interface set to "core side".
- The SMF configures the group-level N4 Session for processing packets received from a 5G VN group member connected via N6 with the following N4 rules.
  - in order to detect the traffic, a PDR containing Source Interface set to "core side" and Source Address set to the IP/MAC address (es) of this 5G VN group member; and
  - in order to forward the traffic, a FAR containing Destination Interface set to "5G VN internal".
- The SMF configures the group-level N4 Session for processing packets towards a 5G VN group member connected via N6 or packets towards a device residing in DN with the following N4 rules.
````

### `24.501:6.4.1.2:14` — random

- spec: TS 24.501 18.14.0 (Rel-18) · section: **6.4.1.2** · title: UE-requested PDU session establishment procedure initiation
- breadcrumb: 6 > 6.4 > 6.4.1 > 6.4.1.2 · content_type: text · part: 14 · tokens: 759

````text
[TS 24.501 §6.4.1.2 UE-requested PDU session establishment procedure initiation | 6 Elementary procedures for 5GS session management > 6.4 UE-requested 5GSM procedures > 6.4.1 UE-requested PDU session establishment procedure]
- e) the request type which is set to:
  - 1) "initial request", if the UE is not registered for emergency services and the UE requests to establish a new non-emergency PDU session;
  - 2) "existing PDU session", if the UE is not registered for emergency services and the UE requests:
    - i) handover of an existing non-emergency PDU session between 3GPP access and non-3GPP access;
    - ii) transfer of an existing PDN connection for non-emergency bearer services in the EPS to the 5GS; or
    - iii) transfer of an existing PDN connection for non-emergency bearer services in an untrusted non-3GPP access connected to the EPC to the 5GS;
  - 3) "initial emergency request", if the UE requests to establish a new emergency PDU session;
  - 4) "existing emergency PDU session", if the UE requests:
    - i) handover of an existing emergency PDU session between 3GPP access and non-3GPP access;
    - ii) transfer of an existing PDN connection for emergency bearer services in the EPS to the 5GS; or
    - iii) transfer of an existing PDN connection for emergency bearer services in an untrusted non-3GPP access connected to the EPC to the 5GS; or
  - 5) "MA PDU request", if:
    - i) the UE requests to establish an MA PDU session;
    - ii) the UE requests to establish user plane resources over other access of an MA PDU session established over one access only; or
    - iii) the UE performs inter-system change from S1 mode to N1 mode according to clause 4.8.2.3.1 and requests transfer of a PDN connection which is a user plane resource of an MA PDU session; and
- f) the old PDU session ID which is the PDU session ID of the existing PDU session, if the UE initiates the UE-requested PDU session establishment procedure upon receiving the PDU SESSION MODIFICATION COMMAND messages with the 5GSM cause IE set to #39 "reactivation requested";
NOTE 13: If the PDU SESSION MODIFICATION COMMAND message included alternative S-NSSAI, the UE includes alternative S-NSSAI in the PDU SESSION ESTABLISHMENT REQUEST message for PDU session re-establishment.
using the NAS transport procedure as specified in clause 5.4.5, and the UE shall start timer T3580 (see example in figure 6.4.1.2.1).
For bullet c) 1), if the matching URSP rule does not have an associated S-NSSAI, or if the UE does not have any matching URSP rule and there is no S-NSSAI in the UE local configuration or in the default URSP rule, the UE shall not provide any S-NSSAI in a PDU session establishment procedure.
For bullet c) 1a), if the selected PDU session parameters for 5G ProSe layer-3 UE-to-network relay UE do not have an associated S-NSSAI, the UE shall not provide any S-NSSAI in a PDU session establishment procedure.
For bullet d) 1),
````
