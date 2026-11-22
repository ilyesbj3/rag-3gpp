# Rel-18 vs Rel-17 answers (config `best`)

*preliminary — gold set pending human validation.* Questions where the two answers cite different sections or where one release refused.

## s23-01 — What is the role of the AMF in the 5G System?

**Rel-18** (§5.27.1.11, §5.9.4, §6.2.1):

> The Access and Mobility Management Function (AMF) includes the following functionality (some or all of which may be supported in a single instance of an AMF):
> 
> * Termination of RAN CP interface (N2) [TS 23.501 §6.2.1].
> * Termination of NAS (N1), NAS ciphering and integrity protection [TS 23.501 §6.2.1].
> * Registration management [TS 23.501 §6.2.1].
> * Connection management [TS 23.501 §6.2.1].
> * Reachability management [TS 23.501 §6.2.1].
> * Mobility Management [TS 23.501 §6.2.1].
> * Lawful intercept (for AMF events and interface to LI System) [TS 23.501 §6.2.1].
> * Provide transport for SM messages between UE and SMF [TS 23.501 §6.2.1].
> * Transparent proxy for routing SM messages [TS 23.501 §6.2.1].
> * Access Authentication [TS 23.501 §6.2.1].
> * Access Authorization [TS 23.501 §6.2.1].
> * Provide transport for SMS messages between UE and SMSF [TS 23.501 §6.2.1].
> * Security Anchor Functionality (SEAF) as specified in TS 33.501 [29] [TS 23.501 §6.2.1].
> * Location Services management for regulatory services [TS 23.501 §6.2.1].
> * Provide transport for Location Services messages between UE and LMF as well as between RAN and LMF [TS 23.501 §6.2.1].
> * EPS Bearer ID allocation for interworking with EPS [TS 23.501 §6.2.1].
> * UE mobility event notification [TS 23.501 §6.2.1].
> * S-NSSAIs per TA mapping notification [TS 23.501 §6.2.1].
> * Support for Control Plane CIoT 5GS Optimisation [TS 23.501 §6.2.1].
> * Support for User Plane CIoT 5GS Optimisation [TS 23.501 §6.2.1].
> * Support for restriction of use of Enhanced Coverage [TS 23.501 §6.2.1].
> * Provisioning of external parameters (Expected UE Behaviour parameters or Network Configuration parameters) [TS 23.501 §6.2.1].
> * Support for Network Slice-Specific Authentication and Authorization [TS 23.501 §6.2.1].
> * Support for charging [TS 23.501 §6.2.1].
> * Controlling the 5G access stratum-based time distribution based on UE's subscription data [TS 23.501 §6.2.1].
> * Controlling the gNB's time synchronization status reporting and subscription [TS 23.501 §6.2.1].
> 
> To support non-3GPP access networks, the AMF may also include the following functionality:
> * Support of N2 interface with N3IWF/TNGF (over which some 3GPP access information/procedures may not apply and non-3GPP access specific information may be applied) [TS 23.501 §6.2.1].
> * Support of NAS signalling with a UE over N3IWF/TNGF (where some procedures supported over 3GPP access may not be applicable to untrusted non-3GPP access, e.g., Paging) [TS 23.501 §6.2.1].
> * Support of authentication of UEs connected over N3IWF/TNGF [TS 23.501 §6.2.1].
> * Management of mobility, authentication, and separate security context state(s) of a UE connected via a non-3GPP access or connected via a 3GPP access and a non-3GPP access simultaneously [TS 23.501 §6.2.1].
> * Support for a co-ordinated RM management context valid over a 3GPP access and a Non-3GPP access [TS 23.501 §6.2.1].
> * Support for dedicated CM management contexts for the UE for connectivity over non-3GPP access [TS 23.501 §6.2.1].
> * Determine whether the serving N3IWF/TNGF is appropriate based on the slices supported by the N3IWFs/TNGFs [TS 23.501 §6.2.1].
> 
> Additionally, the AMF allocates a 5G-GUTI to the UE that is common to both 3GPP and non-3GPP access, and may re-assign a new 5G-GUTI to the UE at any time or under conditions specified in TS 33.501 [29] [TS 23.501 §5.9.4]. During the Registration procedure, the AMF retrieves subscription data from the UDM and uses it to control 5G access stratum-based time distribution if received [TS 23.501 §5.27.1.11].

**Rel-17** (no citation):

> I could not find this information in the documents.

## s23-03 — What functionality does the UPF support?

**Rel-18** (§4.2.10, §5.8.2.14, §5.8.2.17, §5.8.2.6.3, §6.2.3):

> The User plane function (UPF) includes the following functionality (some or all may be supported in a single instance of a UPF):
> 
> - Anchor point for Intra-/Inter-RAT mobility (when applicable) [TS 23.501 §6.2.3].
> - Allocation of UE IP address/prefix (if supported) in response to SMF request [TS 23.501 §6.2.3].
> - External PDU Session point of interconnect to Data Network [TS 23.501 §6.2.3].
> - Packet routing & forwarding (e.g. support of Uplink classifier to route traffic flows to an instance of a data network, support of Branching point to support multi-homed PDU Session, support of traffic forwarding within a 5G VN group (UPF local switching, via N6, via N19)) [TS 23.501 §6.2.3].
> - Packet inspection (e.g. Application detection based on service data flow template and the optional PFDs received from the SMF in addition) [TS 23.501 §6.2.3].
> - User Plane part of policy rule enforcement, e.g. Gating, Redirection, Traffic steering [TS 23.501 §6.2.3].
> - Lawful intercept (UP collection) [TS 23.501 §6.2.3].
> - Traffic usage reporting [TS 23.501 §6.2.3].
> - QoS handling for user plane, e.g. UL/DL rate enforcement, Reflective QoS marking in DL [TS 23.501 §6.2.3].
> - Uplink Traffic verification (SDF to QoS Flow mapping) [TS 23.501 §6.2.3].
> - Transport level packet marking in the uplink and downlink [TS 23.501 §6.2.3].
> - Downlink packet buffering and downlink data notification triggering [TS 23.501 §6.2.3].
> - Sending and forwarding of one or more "end marker" to the source NG-RAN node [TS 23.501 §6.2.3].
> - Functionality to respond to Address Resolution Protocol (ARP) requests and / or IPv6 Neighbour Solicitation requests based on local cache information for the Ethernet PDUs (responding by providing the MAC address corresponding to the IP address sent in the request) [TS 23.501 §6.2.3].
> - Packet duplication in downlink direction and elimination in uplink direction in GTP-U layer [TS 23.501 §6.2.3].
> - NW-TT functionality [TS 23.501 §6.2.3].
> - High latency communication, see clause 5.31.8 of TS 23.501 [TS 23.501 §6.2.3].
> - ATSSS Steering functionality to steer the MA PDU Session traffic, refer to clause 5.32.6 of TS 23.501 [TS 23.501 §6.2.3].
> - Inter PLMN UP Security (IPUPS) functionality, specified in clause 5.8.2.14 of TS 23.501 [TS 23.501 §6.2.3].
> - Event exposure, including exposure of network information (QoS monitoring information, events, data collected for analytics, and TSC management information) [TS 23.501 §6.2.3].
> - Exposure of the UE information (e.g. UE IP address translation information if NAT functionality of the UE IP address is deployed within UPF) [TS 23.501 §6.2.3].
> - Support PDU Set based handling as defined in clause 5.37.5 of TS 23.501 [TS 23.501 §6.2.3].
> - Inter PLMN User Plane Security (IPUPS) functionality at the border of their network to protect their networks from invalid inter PLMN N9 traffic (forwarding GTP-U packets received via N9 only if they belong to an active PDU Session and are not malformed) [TS 23.501 §5.8.2.14].
> - UPF Event Exposure service to expose information directly via a service-based interface [TS 23.501 §5.8.2.17].
> - MPTCP Proxy functionality, communicating with MPTCP functionality in the UE using the MPTCP protocol (IETF RFC 8684) [TS 23.501 §4.2.10].
> - MPQUIC Proxy functionality, communicating with MPQUIC functionality in the UE using the QUIC protocol and its multipath extensions [TS 23.501 §4.2.10].
> - ATSSS-LL functionality [TS 23.501 §4.2.10].
> - Performance Measurement Functionality (PMF), which may be used by the UE to obtain access performance measurements over the user-plane of 3GPP access and/or non-3GPP access [TS 23.501 §4.2.10].
> - Reporting of usage information to the SMF based on different triggers (periodic reporting, usage thresholds, report on demand) [TS 23.501 §5.8.2.6.3].

**Rel-17** (§4.2.10, §4.2.4, §5.12.1, §5.8.2.14, §5.8.2.6.3, §6.2.3):

> The User Plane Function (UPF) includes the following functionalities (some or all may be supported in a single UPF instance):
> 
> - Anchor point for Intra-/Inter-RAT mobility (when applicable) [TS 23.501 §6.2.3].
> - Allocation of UE IP address/prefix (if supported) in response to SMF request [TS 23.501 §6.2.3].
> - External PDU Session point of interconnect to Data Network [TS 23.501 §6.2.3].
> - Packet routing & forwarding (e.g. support of Uplink classifier to route traffic flows to an instance of a data network, support of Branching point to support multi-homed PDU Session, support of traffic forwarding within a 5G VN group (UPF local switching, via N6, via N19)) [TS 23.501 §6.2.3].
> - Packet inspection (e.g. Application detection based on service data flow template and the optional PFDs received from the SMF in addition) [TS 23.501 §6.2.3].
> - User Plane part of policy rule enforcement, e.g. Gating, Redirection, Traffic steering [TS 23.501 §6.2.3].
> - Lawful intercept (UP collection) [TS 23.501 §6.2.3].
> - Traffic usage reporting [TS 23.501 §6.2.3], including collecting and reporting usage data to the SMF based on triggers such as periodic reporting, usage thresholds, or report on demand [TS 23.501 §5.8.2.6.3][TS 23.501 §5.12.1].
> - QoS handling for user plane, e.g. UL/DL rate enforcement, Reflective QoS marking in DL [TS 23.501 §6.2.3].
> - Uplink Traffic verification (SDF to QoS Flow mapping) [TS 23.501 §6.2.3].
> - Transport level packet marking in the uplink and downlink [TS 23.501 §6.2.3].
> - Downlink packet buffering and downlink data notification triggering [TS 23.501 §6.2.3].
> - Sending and forwarding of one or more "end marker" to the source NG-RAN node [TS 23.501 §6.2.3].
> - Functionality to respond to Address Resolution Protocol (ARP) requests and / or IPv6 Neighbour Solicitation requests based on local cache information for the Ethernet PDUs (responding by providing the MAC address corresponding to the IP address sent in the request) [TS 23.501 §6.2.3].
> - Packet duplication in downlink direction and elimination in uplink direction in GTP-U layer [TS 23.501 §6.2.3].
> - NW-TT functionality [TS 23.501 §6.2.3].
> - High latency communication [TS 23.501 §6.2.3].
> - ATSSS Steering functionality to steer the MA PDU Session traffic [TS 23.501 §6.2.3].
> - Inter PLMN UP Security (IPUPS) functionality (which forwards GTP-U packets received via N9 only if they belong to an active PDU Session and are not malformed, and terminates GTP-U N9 tunnels) [TS 23.501 §6.2.3][TS 23.501 §5.8.2.14][TS 23.501 §4.2.4].
> - Exposure of network information, i.e., the QoS monitoring information, as specified in clause 6.4 of TS 23.548 [130] [TS 23.501 §6.2.3].
> - MPTCP Proxy functionality, communicating with MPTCP in the UE [TS 23.501 §4.2.10].
> - ATSSS-LL functionality (similar to the ATSSS-LL functionality defined for the UE; needed in 5GC for MA PDU Session of type Ethernet) [TS 23.501 §4.2.10].
> - Performance Measurement Functionality (PMF), which may be used by the UE to obtain access performance measurements over the user-plane of 3GPP and/or non-3GPP access [TS 23.501 §4.2.10].
> 
> *(Note: Not all UPF functionalities are required to be supported in an instance of user plane function of a Network Slice [TS 23.501 §6.2.3].)*

