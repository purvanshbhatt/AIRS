const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'src', 'api.ts');
let content = fs.readFileSync(filePath, 'utf8');

const regex = /new ApiRequestError\(\{\s*(message:[^,]+),\s*(status:\s*([^,}]+))?/g;

content = content.replace(regex, (match, messagePart, statusPart, statusCode) => {
    let kind = "'server'";
    if (!statusPart) {
        kind = "'network'";
    } else if (statusCode === '401') {
        kind = "'unauthorized'";
    } else if (statusCode === '403') {
        kind = "'forbidden'";
    } else if (statusCode === '404') {
        kind = "'not_found'";
    }

    if (statusPart) {
        return `new ApiRequestError({\n      kind: ${kind},\n      ${messagePart},\n      ${statusPart}`;
    } else {
        return `new ApiRequestError({\n      kind: ${kind},\n      ${messagePart}`;
    }
});

fs.writeFileSync(filePath, content, 'utf8');
console.log('Fixed ApiRequestError instantiations.');
