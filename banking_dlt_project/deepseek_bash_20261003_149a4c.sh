# Create the files
touch .gitignore .gitattributes .env.example

# Paste the contents above into each

# Clean up any already-tracked files that now match
git rm -r --cached . > /dev/null
git add .
git commit -m "chore: add .gitignore, .gitattributes, .env.example"


#One-liner verification — ensure nothing sensitive is currently tracked:

#bash
#git ls-files | grep -E '\.(env|tfvars|tfstate|pem|key)$|\.databrickscfg$'
#If that returns nothing, you're clean. If it returns filenames, remove them:

#bash
#git rm --cached path/to/offending/file