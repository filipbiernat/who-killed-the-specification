%setdefault('stylesheet', 'spec.css')
%setdefault('is_doc', False)
% tmpRef = '../' if is_doc else ''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{doc_attributes["name"]}}</title>
<link rel="stylesheet" href="{{baseurl}}{{tmpRef}}template/{{stylesheet}}">
</head>
<body>
{{!base}}
</body>
</html>
