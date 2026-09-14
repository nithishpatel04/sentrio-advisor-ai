public with sharing class AdvisorBriefingController {

    // =========================================================
    // DTOs - Clean JSON contract sent from Salesforce to AWS
    // =========================================================

    public class CRMEvidenceDTO {
        public String household_external_id;
        public String household_name;

        // Household risk information used by deterministic rules
        public String risk_profile;
        public Date risk_profile_last_reviewed;

        public List<ContactDTO> contacts = new List<ContactDTO>();
        public List<CaseDTO> cases = new List<CaseDTO>();
        public List<OpportunityDTO> opportunities = new List<OpportunityDTO>();
        public List<TaskDTO> tasks = new List<TaskDTO>();
        public List<EventDTO> events = new List<EventDTO>();
    }


    public class ContactDTO {
        public String client_external_id;
        public String first_name;
        public String last_name;
        public String email;
        public String phone;
        public String title;
    }


    public class CaseDTO {
        public String service_request_external_id;
        public String case_number;
        public String subject;
        public String status;
        public String priority;
        public String origin;
    }


    public class OpportunityDTO {
        public String opportunity_external_id;
        public String name;
        public String stage;
        public Date close_date;
        public Decimal amount;
        public Decimal probability;
        public String type;
    }


    public class TaskDTO {
        public String activity_external_id;
        public String subject;
        public String status;
        public String priority;
        public Date activity_date;
    }


    public class EventDTO {
        public String activity_external_id;
        public String subject;
        public String start_datetime;
        public String end_datetime;
        public String location;
    }


    // =========================================================
    // 1. Retrieve CRM evidence from Salesforce
    // =========================================================

    public static CRMEvidenceDTO getCRMEvidence(
        String householdExternalId
    ) {

        // -----------------------------------------------------
        // Household
        // -----------------------------------------------------

        Account household = [
            SELECT Id,
                   Name,
                   Household_External_ID__c,
                   Client_Since__c,
                   Client_Tier__c,
                   Risk_Profile__c,
                   Risk_Profile_Last_Reviewed__c,
                   Preferred_Contact_Method__c
            FROM Account
            WHERE Household_External_ID__c = :householdExternalId
            LIMIT 1
        ];


        // -----------------------------------------------------
        // Contacts
        // -----------------------------------------------------

        List<Contact> contactRecords = [
            SELECT Id,
                   FirstName,
                   LastName,
                   Email,
                   Phone,
                   Title,
                   Client_External_ID__c
            FROM Contact
            WHERE AccountId = :household.Id
        ];


        // -----------------------------------------------------
        // Cases / Service Requests
        // -----------------------------------------------------

        List<Case> caseRecords = [
            SELECT Id,
                   CaseNumber,
                   Subject,
                   Status,
                   Priority,
                   Origin,
                   ContactId,
                   Service_Request_External_ID__c
            FROM Case
            WHERE AccountId = :household.Id
        ];


        // -----------------------------------------------------
        // Opportunities
        // -----------------------------------------------------

        List<Opportunity> opportunityRecords = [
            SELECT Id,
                   Name,
                   StageName,
                   CloseDate,
                   Amount,
                   Probability,
                   Type,
                   Opportunity_External_ID__c
            FROM Opportunity
            WHERE AccountId = :household.Id
        ];


        // -----------------------------------------------------
        // Tasks
        // -----------------------------------------------------

        List<Task> taskRecords = [
            SELECT Id,
                   Subject,
                   Status,
                   Priority,
                   ActivityDate,
                   WhoId,
                   WhatId,
                   Activity_External_ID__c
            FROM Task
            WHERE WhatId = :household.Id
        ];


        // -----------------------------------------------------
        // Events / Meetings
        // -----------------------------------------------------

        List<Event> eventRecords = [
            SELECT Id,
                   Subject,
                   StartDateTime,
                   EndDateTime,
                   Location,
                   WhoId,
                   WhatId,
                   Activity_External_ID__c
            FROM Event
            WHERE WhatId = :household.Id
            ORDER BY StartDateTime DESC
        ];


        // =====================================================
        // Build clean CRM evidence DTO
        // =====================================================

        CRMEvidenceDTO evidence = new CRMEvidenceDTO();


        // -----------------------------------------------------
        // Household information
        // -----------------------------------------------------

        evidence.household_external_id =
            household.Household_External_ID__c;

        evidence.household_name =
            household.Name;

        evidence.risk_profile =
            household.Risk_Profile__c;

        evidence.risk_profile_last_reviewed =
            household.Risk_Profile_Last_Reviewed__c;


        // -----------------------------------------------------
        // Contacts
        // -----------------------------------------------------

        for (Contact record : contactRecords) {

            ContactDTO dto = new ContactDTO();

            dto.client_external_id =
                record.Client_External_ID__c;

            dto.first_name =
                record.FirstName;

            dto.last_name =
                record.LastName;

            dto.email =
                record.Email;

            dto.phone =
                record.Phone;

            dto.title =
                record.Title;

            evidence.contacts.add(dto);
        }


        // -----------------------------------------------------
        // Cases
        // -----------------------------------------------------

        for (Case record : caseRecords) {

            CaseDTO dto = new CaseDTO();

            dto.service_request_external_id =
                record.Service_Request_External_ID__c;

            dto.case_number =
                record.CaseNumber;

            dto.subject =
                record.Subject;

            dto.status =
                record.Status;

            dto.priority =
                record.Priority;

            dto.origin =
                record.Origin;

            evidence.cases.add(dto);
        }


        // -----------------------------------------------------
        // Opportunities
        // -----------------------------------------------------

        for (Opportunity record : opportunityRecords) {

            OpportunityDTO dto = new OpportunityDTO();

            dto.opportunity_external_id =
                record.Opportunity_External_ID__c;

            dto.name =
                record.Name;

            dto.stage =
                record.StageName;

            dto.close_date =
                record.CloseDate;

            dto.amount =
                record.Amount;

            dto.probability =
                record.Probability;

            dto.type =
                record.Type;

            evidence.opportunities.add(dto);
        }


        // -----------------------------------------------------
        // Tasks
        // -----------------------------------------------------

        for (Task record : taskRecords) {

            TaskDTO dto = new TaskDTO();

            dto.activity_external_id =
                record.Activity_External_ID__c;

            dto.subject =
                record.Subject;

            dto.status =
                record.Status;

            dto.priority =
                record.Priority;

            dto.activity_date =
                record.ActivityDate;

            evidence.tasks.add(dto);
        }


        // -----------------------------------------------------
        // Events
        // -----------------------------------------------------

        for (Event record : eventRecords) {

            EventDTO dto = new EventDTO();

            dto.activity_external_id =
                record.Activity_External_ID__c;

            dto.subject =
                record.Subject;

            if (record.StartDateTime != null) {

                dto.start_datetime =
                    record.StartDateTime.formatGMT(
                        'yyyy-MM-dd\'T\'HH:mm:ss\'Z\''
                    );
            }


            if (record.EndDateTime != null) {

                dto.end_datetime =
                    record.EndDateTime.formatGMT(
                        'yyyy-MM-dd\'T\'HH:mm:ss\'Z\''
                    );
            }


            dto.location =
                record.Location;

            evidence.events.add(dto);
        }


        return evidence;
    }


    // =========================================================
    // 2. Generate combined evidence through AWS
    // =========================================================
    @AuraEnabled
    public static String generateEvidence(
        String householdExternalId
    ) {

        // -----------------------------------------------------
        // Retrieve actual Salesforce CRM information
        // -----------------------------------------------------

        CRMEvidenceDTO crmEvidence =
            getCRMEvidence(householdExternalId);


        // -----------------------------------------------------
        // Convert CRM DTO to JSON
        // -----------------------------------------------------

        String requestBody =
            JSON.serialize(crmEvidence);


        System.debug(
            'Generating briefing evidence for household: '
            + householdExternalId
        );


        // =====================================================
        // AWS HTTP Callout
        // =====================================================

        HttpRequest request =
            new HttpRequest();


        // Named Credential created earlier
        request.setEndpoint(
            'callout:Sentrio_AWS_API/briefings/evidence'
        );


        request.setMethod(
            'POST'
        );


        request.setHeader(
            'Content-Type',
            'application/json'
        );


        request.setBody(
            requestBody
        );


        request.setTimeout(
            20000
        );


        Http http =
            new Http();


        HttpResponse response =
            http.send(request);


        System.debug(
            'AWS STATUS CODE: '
            + response.getStatusCode()
        );


        // =====================================================
        // Successful AWS response
        // =====================================================

        if (
            response.getStatusCode() >= 200 &&
            response.getStatusCode() < 300
        ) {

            return response.getBody();
        }


        // =====================================================
        // AWS error
        // =====================================================

        throw new CalloutException(
            'Unable to generate briefing evidence. '
            + 'AWS returned HTTP '
            + response.getStatusCode()
        );
    }
}