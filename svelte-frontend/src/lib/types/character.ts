export type CharacterAnalysisStatus = 'pending' | 'running' | 'done' | 'failed' | null;

export interface CharacterSummary {
	name: string;
	slug: string;
	role: string;
}

export interface CharacterRelation {
	to_slug: string;
	to_name: string;
	type: string;
	type_display: string;
	group: string;
}

export interface CharacterDetail extends CharacterSummary {
	description: string;
	relations: CharacterRelation[];
}

export interface CharacterListResponse {
	status: CharacterAnalysisStatus;
	characters: CharacterSummary[];
}
