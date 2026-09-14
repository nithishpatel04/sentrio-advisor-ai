import { LightningElement, api, wire } from 'lwc';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';
import generateEvidence from '@salesforce/apex/AdvisorBriefingController.generateEvidence';
import ACCOUNT_NAME from '@salesforce/schema/Account.Name';
import HOUSEHOLD_EXTERNAL_ID from '@salesforce/schema/Account.Household_External_ID__c';

const ACCOUNT_FIELDS = [ACCOUNT_NAME, HOUSEHOLD_EXTERNAL_ID];

const SECTION_DEFINITIONS = [
    { key: 'executive_summary', label: 'Executive Summary' },
    { key: 'client_household_overview', label: 'Client & Household Overview' },
    { key: 'key_changes_since_last_meeting', label: 'Key Changes Since Last Meeting' },
    { key: 'risks_attention', label: 'Risks & Attention', emphasized: true },
    { key: 'recommended_discussion_topics', label: 'Recommended Discussion Topics' },
    { key: 'open_actions_followups', label: 'Open Actions & Follow-Ups' },
    { key: 'data_gaps_uncertainty', label: 'Data Gaps & Uncertainty' }
];

export default class AdvisorBriefing extends LightningElement {
    @api recordId;

    account;
    briefing;
    errorMessage;
    isBusy = false;
    generatedAt;

    @wire(getRecord, { recordId: '$recordId', fields: ACCOUNT_FIELDS })
    wiredAccount({ data, error }) {
        if (data) {
            this.account = data;
            this.errorMessage = this.householdExternalId
                ? undefined
                : 'This Account does not have a Household External ID.';
        } else if (error) {
            this.account = undefined;
            this.errorMessage = 'Unable to load the household account details.';
        }
    }

    get accountName() {
        return this.account ? getFieldValue(this.account, ACCOUNT_NAME) : '';
    }

    get householdExternalId() {
        return this.account ? getFieldValue(this.account, HOUSEHOLD_EXTERNAL_ID) : '';
    }

    get buttonLabel() {
        return this.briefing ? 'Regenerate Briefing' : 'Generate Briefing';
    }

    get hasBriefing() {
        return Boolean(this.briefing);
    }

    get isDisabled() {
        return this.isBusy || !this.householdExternalId;
    }

    get generatedLabel() {
        return this.generatedAt ? this.generatedAt.toLocaleString() : '';
    }

    get sections() {
        if (!this.briefing) {
            return [];
        }

        return SECTION_DEFINITIONS.map((definition) => ({
            ...definition,
            items: this.normalizeSection(this.briefing[definition.key]),
            hasItems: this.normalizeSection(this.briefing[definition.key]).length > 0,
            cssClass: definition.emphasized ? 'briefing-section attention' : 'briefing-section'
        }));
    }

    get citations() {
        const citations = this.briefing?.citations;
        if (!Array.isArray(citations)) {
            return [];
        }

        return citations.map((citation, index) => ({
            key: `${citation.source_type || 'source'}-${index}`,
            sourceType: citation.source_type || 'Unknown source',
            sourceIds: Array.isArray(citation.source_ids) ? citation.source_ids.join(', ') : ''
        }));
    }

    get hasCitations() {
        return this.citations.length > 0;
    }

    async handleGenerate() {
        if (this.isBusy) {
            return;
        }

        if (!this.householdExternalId) {
            this.errorMessage = 'This Account does not have a Household External ID.';
            return;
        }

        this.isBusy = true;
        this.errorMessage = undefined;

        try {
            const response = await generateEvidence({
                householdExternalId: this.householdExternalId
            });
            const payload = this.parseResponse(response);
            if (!payload.advisor_briefing || typeof payload.advisor_briefing !== 'object') {
                throw new Error('The service did not return a valid advisor briefing.');
            }
            this.briefing = payload.advisor_briefing;
            this.generatedAt = new Date();
        } catch (error) {
            this.briefing = undefined;
            this.generatedAt = undefined;
            this.errorMessage = this.readableError(error);
        } finally {
            this.isBusy = false;
        }
    }

    parseResponse(response) {
        if (typeof response === 'string') {
            const parsed = JSON.parse(response);
            if (typeof parsed === 'string') {
                return JSON.parse(parsed);
            }
            return parsed;
        }

        if (response && typeof response === 'object') {
            return response;
        }

        throw new Error('The service returned an unexpected response.');
    }

    normalizeSection(value) {
        if (Array.isArray(value)) {
            return value.map((item) => this.itemToText(item)).filter(Boolean);
        }
        if (typeof value === 'string' && value.trim()) {
            return [value.trim()];
        }
        return [];
    }

    itemToText(item) {
        if (typeof item === 'string' || typeof item === 'number') {
            return String(item);
        }
        if (item && typeof item === 'object') {
            if (typeof item.statement === 'string') {
                return item.statement;
            }
            return Object.values(item).filter((value) => typeof value === 'string' || typeof value === 'number').join(' - ');
        }
        return '';
    }

    readableError(error) {
        const body = error?.body;
        if (typeof body?.message === 'string') {
            return body.message;
        }
        if (typeof body?.detail === 'string') {
            return body.detail;
        }
        if (typeof error?.message === 'string' && error.message) {
            return error.message;
        }
        return 'Unable to generate the advisor briefing. Please try again or contact your Salesforce administrator.';
    }
}
