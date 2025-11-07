#!/bin/bash

# Script to upload sample files to different departments
# Make sure the API server is running before executing this script

API_BASE="http://localhost:8000"

echo "🧪 Uploading Sample Files to Different Departments"
echo "================================================="

# Department arrays (using indexed arrays instead of associative)
DEPARTMENTS=(
    "Computer Science & Engineering"
    "Mechanical Engineering" 
    "Electronics & Communication"
    "Civil Engineering"
    "Electrical Engineering"
    "Chemical Engineering"
    "Biotechnology"
    "Information Technology"
)

USERS=(
    "arjun_cs:password123"
    "priya_me:password123" 
    "krishna_ece:password123"
    "vishnu_ce:password123"
    "sai_ee:password123"
    "arun_ch:password123"
    "kavya_bt:password123"
    "divya_it:password123"
)

FILES=(
    "sample_files/cs_data_structures.txt"
    "sample_files/me_thermodynamics.txt"
    "sample_files/ece_signal_processing.txt"
    "sample_files/ce_structural_analysis.txt"
    "sample_files/ee_power_systems.txt"
    "sample_files/ch_process_control.txt"
    "sample_files/bt_molecular_biology.txt"
    "sample_files/it_database_systems.txt"
)

DESCRIPTIONS=(
    "Comprehensive study notes covering Data Structures and Algorithms including trees, graphs, sorting algorithms, and dynamic programming concepts essential for competitive programming and interviews."
    "Detailed reference material on Engineering Thermodynamics covering laws of thermodynamics, thermodynamic processes, heat engines, refrigeration cycles, and practical applications in power plants and automotive systems."
    "Complete guide to Digital Signal Processing including discrete-time signals, Z-transforms, digital filters, DFT/FFT, and applications in audio processing, communications, and image processing."
    "In-depth coverage of Structural Analysis methods including statically determinate/indeterminate structures, influence lines, moment distribution, plastic analysis, and modern analysis software applications."
    "Comprehensive material on Power Systems Analysis covering per-unit systems, load flow analysis, fault analysis, stability studies, protection systems, and renewable energy integration challenges."
    "Complete reference on Process Control and Instrumentation including control system fundamentals, PID controllers, advanced control strategies, process instrumentation, and industrial applications in chemical processes."
    "Extensive notes on Molecular Biology and Genetic Engineering covering DNA structure/replication, gene expression, recombinant DNA technology, PCR, protein expression systems, CRISPR, and biotechnology applications."
    "Thorough coverage of Database Management Systems including database models, SQL, ER modeling, normalization, transaction management, indexing, and emerging technologies like NoSQL and cloud databases."
)

uploaded_files=0
failed_uploads=0

# Function to get authentication token
get_token() {
    local credentials=$1
    local username=$(echo $credentials | cut -d: -f1)
    local password=$(echo $credentials | cut -d: -f2)
    
    local response=$(curl -s -X POST "$API_BASE/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\": \"$username\", \"password\": \"$password\"}")
    
    echo $response | python3 -c "
try:
    import sys, json
    data = json.load(sys.stdin)
    print(data.get('access_token', ''))
except:
    print('')
" 2>/dev/null
}

# Upload files for each department
for i in "${!DEPARTMENTS[@]}"; do
    dept="${DEPARTMENTS[$i]}"
    credentials="${USERS[$i]}"
    file_path="${FILES[$i]}"
    description="${DESCRIPTIONS[$i]}"
    
    echo ""
    echo "📁 Processing Department: $dept"
    echo "----------------------------------------"
    
    # Check if file exists
    if [ ! -f "$file_path" ]; then
        echo "❌ File not found: $file_path"
        ((failed_uploads++))
        continue
    fi
    
    # Get authentication token
    echo "🔐 Getting authentication token..."
    token=$(get_token "$credentials")
    
    if [ -z "$token" ]; then
        echo "❌ Authentication failed for $dept"
        ((failed_uploads++))
        continue
    fi
    
    echo "✅ Authentication successful"
    echo "Token: ${token:0:50}..."
    
    # Upload file
    echo "📤 Uploading file: $file_path"
    
    upload_response=$(curl -s -X POST "$API_BASE/files/upload" \
        -H "Authorization: Bearer $token" \
        -F "file=@$file_path" \
        -F "description=$description")
    
    # Check if upload was successful
    file_id=$(echo $upload_response | python3 -c "
try:
    import sys, json
    data = json.load(sys.stdin)
    if 'id' in data:
        print(data['id'])
    else:
        print('')
except:
    print('')
" 2>/dev/null)
    
    if [ ! -z "$file_id" ]; then
        echo "✅ Upload successful! File ID: $file_id"
        filename=$(echo $upload_response | python3 -c "
try:
    import sys, json
    data = json.load(sys.stdin)
    print(data.get('original_filename', 'unknown'))
except:
    print('unknown')
" 2>/dev/null)
        echo "   📄 Original filename: $filename"
        ((uploaded_files++))
    else
        echo "❌ Upload failed for $dept"
        echo "   Response: $upload_response"
        ((failed_uploads++))
    fi
done

echo ""
echo "📊 UPLOAD SUMMARY"
echo "================="
echo "✅ Successful uploads: $uploaded_files"
echo "❌ Failed uploads: $failed_uploads"
echo "📁 Total departments processed: ${#DEPARTMENTS[@]}"

if [ $uploaded_files -gt 0 ]; then
    echo ""
    echo "🎯 Testing file listing..."
    # Get a token to test file listing
    test_token=$(get_token "${USERS[0]}")
    if [ ! -z "$test_token" ]; then
        files_response=$(curl -s -X GET "$API_BASE/files/" -H "Authorization: Bearer $test_token")
        file_count=$(echo $files_response | python3 -c "
try:
    import sys, json
    data = json.load(sys.stdin)
    print(data.get('total_count', 0))
except:
    print(0)
" 2>/dev/null)
        echo "📋 Total files in system: $file_count"
        
        # Test department stats
        stats_response=$(curl -s -X GET "$API_BASE/files/stats/summary" -H "Authorization: Bearer $test_token")
        echo "📈 File statistics: $stats_response"
    fi
fi

echo ""
echo "🚀 File upload process completed!"
echo ""
echo "💡 You can now test the API endpoints:"
echo "   • GET /files/ - List all files"
echo "   • GET /files/?department=Computer%20Science%20%26%20Engineering - Filter by department"
echo "   • GET /files/{id} - Get specific file details"
echo "   • GET /files/{id}/download - Download file"
echo "   • GET /files/departments/list - List all departments"
echo "   • GET /files/stats/summary - Get file statistics"