export interface CognitoAttributes {
  Name: string;
  Value: string;
}

export interface UnicornUser {
  username: string;
  attributes: UnicornAttributes;
}

export interface UnicornAttributes {
  [key: string]: string;
}

export interface CognitoUser {
  username: string;
  attributes: CognitoAttributes[];
}

export interface RequestStatus {
  status: string;
  message: string;
}