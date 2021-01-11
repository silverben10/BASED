import tokenize
import os
from . import cfg
from ..lib.emojis import UninitializedBasedEmoji
import tomlkit

ignoredVarNames = ("__name__", "__doc__", "__package__", "__loader__", "__spec__", "__file__", "__cached__", "__builtins__", "UninitializedBasedEmoji")
emojiVars = []
emojiListVars = []

for varname, varvalue in cfg.defaultEmojis.items():
    if type(varvalue) == UninitializedBasedEmoji:
        emojiVars.append(varname)
        continue
    elif type(varvalue) == list:
        onlyEmojis = True
        for item in varvalue:
            if type(item) != UninitializedBasedEmoji:
                onlyEmojis = False
                break
        if onlyEmojis:
            emojiListVars.append(varname)
            continue
    raise ValueError("Invalid config variable in cfg.defaultEmojis: Emoji config variables must be either UninitializedBasedEmoji or List[UninitializedBasedEmoji]")


class ConfigProxy:
    def __init__(self, attrs):
        self.attrNames = attrs.keys()
        for varname, varvalue in attrs.items():
            setattr(self, varname, varvalue)


with open('bot/cfg/cfg.py', 'rb') as fileObj:
    inDict = []

    tokens = [ConfigProxy({"type": toktype, "value": tok, "start": start, "end": end, "line": line})
                            for toktype, tok, start, end, line in tokenize.tokenize(fileObj.readline)]
    numTokens = len(tokens)

    docs = {tok.value: ConfigProxy({"prev": [], "inline": ""}) for tok in tokens if tok.type == tokenize.NAME and tok.value not in ignoredVarNames}

    for tokNum in range(len(tokens)):
        tok = tokens[tokNum]
        # print(tokenize.tok_name[tok.type], tok.value)

        # if tok.type == tokenize.OP:
        #     if tok.value == "{":
        #         if tokNum != 0:
        #             prevTokNum = 1
        #             prevToken = tokens[tokNum-prevTokNum]
        #             while prevToken.start[0] == tok.start[0]:
        #                 prevTokNum += 1
        #                 prevToken = tokens[tokNum-prevTokNum]
        #             if prevToken.start[0] != tok.start[0]:
        #                 prevToken = tokens[tokNum-(prevTokNum-1)]

        #             if prevToken.type == tokenize.NAME and prevToken.start[0] == tok.start[0]:
        #                 inDict.append(prevToken.value)
        #     elif tok.value == "}":
        #         inDict.pop()


        # elif tok.type == tokenize.COMMENT:
        if tok.type == tokenize.COMMENT:
            if inDict != []:
                pass
                # prevTokNum = 1
                # prevToken = tokens[tokNum-prevTokNum]
                # while prevToken.start[0] == tok.start[0]:
                #     prevTokNum += 1
                #     prevToken = tokens[tokNum-prevTokNum]
                # if prevToken.start[0] != tok.start[0]:
                #     prevToken = tokens[tokNum-(prevTokNum-1)]

                # if prevToken.type == tokenize.STRING and prevToken.start[0] == tok.start[0]:
                #     currentLevel = docs
                #     for levelName in inDict:
                #         currentLevel
                #     docs[prevToken.value].inline = tok.value.lstrip("# ")
                #     continue
                
                # nextTokNum = tokNum + 2
                # nextToken = None
                # while nextTokNum < numTokens:
                #     if tokens[nextTokNum].type == tokenize.COMMENT:
                #         nextTokNum += 2
                #     nextToken = tokens[nextTokNum]
                #     if tokens[nextTokNum].type != tokenize.COMMENT:
                #         break
                    
                # if nextTokNum < numTokens and nextToken is not None and nextToken.type == tokenize.NAME:
                #     docs[nextToken.value].prev.append(tok.value.lstrip("# "))
                #     continue
            else:
                if tokNum != 0:
                    prevTokNum = 1
                    prevToken = tokens[tokNum-prevTokNum]
                    while prevToken.start[0] == tok.start[0]:
                        prevTokNum += 1
                        prevToken = tokens[tokNum-prevTokNum]
                    if prevToken.start[0] != tok.start[0]:
                        prevToken = tokens[tokNum-(prevTokNum-1)]

                    if prevToken.type == tokenize.NAME and prevToken.start[0] == tok.start[0]:
                        docs[prevToken.value].inline = tok.value.lstrip("# ")
                        continue
                
                nextTokNum = tokNum + 2
                nextToken = None
                while nextTokNum < numTokens:
                    if tokens[nextTokNum].type == tokenize.COMMENT:
                        nextTokNum += 2
                    nextToken = tokens[nextTokNum]
                    if tokens[nextTokNum].type != tokenize.COMMENT:
                        break
                    
                if nextTokNum < numTokens and nextToken is not None and nextToken.type == tokenize.NAME:
                    docs[nextToken.value].prev.append(tok.value.lstrip("# "))
                    continue

emptyvars = []
for var in docs:
    if docs[var].prev == [] and docs[var].inline == "":
        emptyvars.append(var)
for var in emptyvars:
    del docs[var]

# for var in docs:
#     print(var + ": PREV: " + ((", ".join("'" + prevDoc + "'" for prevDoc in docs[var].prev)) if len(docs[var].prev) > 0 else "''") + " INLINE: '" + docs[var].inline + "'")


def tableFromDict(d):
    newTable = tomlkit.table()
    for var in d:
        if type(d[var]) == dict:
            newTable[var] = tableFromDict(d[var])
        elif type(d[var]) == tuple:
            newTable[var] = list(d[var])
        else:
            newTable[var] = d[var]
    return newTable


# print("Extracted",len(docs),"comments:")
# print("\n" + "\n".join(": ".join((var, ", ".join(comments))) for var, comments in docs.items()))

def makeDefaultCfg(fileName="defaultCfg.toml"):
    if not fileName.endswith(".toml"):
        raise ValueError("file name must end with .toml")

    fileName = os.path.abspath(os.path.normpath(fileName))
    if not os.path.isdir(os.path.dirname(fileName)):
        os.makedirs(os.path.dirname(fileName))
    
    fileName = fileName.split(".toml")[0]
    cfgPath = fileName
    fileExt = ".toml"

    currentExt = 0
    while os.path.exists(cfgPath + fileExt):
        currentExt += 1
        cfgPath = fileName + "-" + str(currentExt)

    cfgPath += fileExt

    defaults = {varname: varvalue for varname, varvalue in vars(cfg).items() if varname not in ignoredVarNames}
    for varname in emojiVars:
        defaults["defaultEmojis"][varname] = cfg.defaultEmojis[varname].value
    
    for varname in emojiListVars:
        working = []
        for item in defaults["defaultEmojis"][varname]:
            working.append(item.value)
            
        defaults["defaultEmojis"][varname] = working

    newDoc = tomlkit.document()
    for var in defaults:
        if type(defaults[var]) != dict:
            if var in docs:
                if docs[var].prev != []:
                    newDoc.add(tomlkit.nl())
                    for prevComment in docs[var].prev:
                        print("ADDING PREV TO ",var,":",prevComment)
                        newDoc.add(tomlkit.comment(prevComment))
            print("ADDING VAR",var)
            if type(defaults[var]) == tuple:
                newDoc[var] = list(defaults[var])
            else:
                newDoc[var] = defaults[var]
            if var in docs and docs[var].inline != "":
                print("ADDING INLINE TO ",var,":",docs[var].inline)
                newDoc[var].comment(docs[var].inline)
    

    for var in defaults:
        if type(defaults[var]) == dict:
            if var in docs and docs[var].prev != []:
                newDoc.add(tomlkit.nl())
            if var in docs:
                for prevComment in docs[var].prev:
                    print("ADDING PREV TO ",var,":",prevComment)
                    newDoc.add(tomlkit.comment(prevComment))
            print("ADDING VAR",var)
            newDoc[var] = tableFromDict(defaults[var])
        
    
    # return defaults

    with open(cfgPath, "w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(newDoc).lstrip("\n"))

    print("Created " + cfgPath)