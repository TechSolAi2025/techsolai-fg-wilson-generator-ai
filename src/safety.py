import re
INJECTION=re.compile(r'(?is)(ignore|override|bypass|disregard|forget).{0,60}(instruction|manual|safety|system|previous|rule)|reveal.{0,30}(prompt|secret)|(?:system|assistant|developer)\s*[:>]|<\|(?:im_start|system)|pretend.{0,40}(source|manual)|invent.{0,30}(answer|fault|citation)')
UNSAFE_REQUEST=re.compile(r'(?is)(bypass|disable|defeat|jumper|short|bridge|remove).{0,50}(safety|interlock|shutdown|breaker|guard|protection)|(?:run|operate).{0,30}(?:without|remove).{0,25}guard|(?:run|operate).{0,40}guards?.{0,15}(?:removed|off)|inducement override')
OUTSIDE=re.compile(r'(?i)\b(?:resuscitation|cpr|medical treatment|chest compression)\b')
SERVICE=re.compile(r'(?i)\b(?:overhaul|disassembl\w*|pinout|wiring[- ](?:level|diagram)|internal[- ](?:engine|controller)|engine[- ]rebuild|injector[- ](?:repair|torque)|component[- ](?:disassembly|teardown)|terminal\s+\d+|sensor[- ]calibration|controller[- ]internal)\b')
UNSUPPORTED_DIAGNOSTICS=re.compile(r'(?i)\b(?:SPN|FMI|factory\s+(?:reset|defaults?)|recalibrat\w*|numerical\s+fault[- ]code\s+dictionary)\b')
def query_block_reason(query):
    if INJECTION.search(query): return 'Prompt-injection attempt rejected.'
    if UNSAFE_REQUEST.search(query): return 'Safety-control bypass request rejected.'
    if SERVICE.search(query) or UNSUPPORTED_DIAGNOSTICS.search(query): return 'Outside V1 service scope; obtain the exact equipment service manual and qualified dealer support.'
    if OUTSIDE.search(query): return 'Outside generator technical answering scope.'
    return None

def document_block_reason(text):
    return 'Document instruction injection quarantined' if INJECTION.search(text) else None
