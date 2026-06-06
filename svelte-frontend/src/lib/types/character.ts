export type CharacterAnalysisStatus = 'pending' | 'running' | 'done' | 'failed' | null;

export interface CharacterSummary {
	name: string;
	slug: string;
	role: string;
}

export interface CharacterRelation {
	to_slug: string;
	to_name: string;
	label: string;
}

export interface CharacterDetail extends CharacterSummary {
	description: string;
	relations: CharacterRelation[];
}

export interface CharacterListResponse {
	status: CharacterAnalysisStatus;
	characters: CharacterSummary[];
}
