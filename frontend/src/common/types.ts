export interface Document {
  documentid: string;
  userid: string;
  filename: string;
  filesize: string;
  docstatus: string;
  created: string;
  pages: string;
  conversations: {
    conversationid: string;
    created: string;
  }[];
}

export interface Conversation {
  messages: {
    type: string;
    content: string;
  }[];
}

export interface Attribute {
  attributes: {
    name: string;
    value: string;
  }[];
}
