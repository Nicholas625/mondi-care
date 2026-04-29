const input = document.getElementById("imageInput");
const preview = document.getElementById("previewImg");

if(input){
    input.addEventListener("change", function(){
        const file = this.files[0];
        if(file){
            const reader = new FileReader();
            reader.onload = function(e){
                preview.src = e.target.result;
            }
            reader.readAsDataURL(file);
        }
    });
}