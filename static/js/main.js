$(function() {

    $(".sortable-list").sortable();

    <!-- UI Add todo list -->
    $(".add-list").click( function(){

        var numList = $('.accordion-header').length;
        console.log(numList);

        if (numList < 5) {
            idLabel = "a" + Math.floor(Math.random() * 10000).toString();
            idAccArea = "a" + Math.floor(Math.random() * 10000).toString();
            console.log(idLabel);
            console.log(idAccArea);

            divGroup = document.createElement("div");
            divGroup.classList.add("accordion-item");
            divGroup.classList.add("group");

            divGroup.innerHTML = "<h2 class=\"accordion-header d-flex\" id=\"" + idLabel + "\">" +
                                 "<i class=\"fa-solid fa-trash-can del-list-icon p-3\"></i>" +
                                 "<input type=\"text\" class=\"form-control-plaintext w-300\" value=\"New Todo List\">" +
                                 "<button class=\"accordion-button p-3\" type=\"button\" data-bs-toggle=\"collapse\" data-bs-target=\"#" + idAccArea + "\" aria-expanded=\"true\" aria-controls=\"" + idAccArea + "\">" +
                                 "</button>" +
                                 "</h2>";

            divCollapse = document.createElement("div");
            divCollapse.classList.add("accordion-collapse");
            divCollapse.classList.add("collapse");
            divCollapse.classList.add("show");
            divCollapse.setAttribute("id", idAccArea);
            divCollapse.setAttribute("aria-labelledby", idLabel);

            divAcc = document.createElement("div");
            divAcc.classList.add("accordion-body");
            divAcc.innerHTML = "<div class=\"list-box\">" +
                               "<input class=\"tasks\" type=\"text\" placeholder=\"Add task here...\"/> <i class=\"fa-solid fa-plus add-icon\"></i>" +
                               "<ul class=\"sortable-list\"></ul>" +
                               "</div>";
            console.log($('#user_exist').data("user"));
            if ( $('#user_exist').data("user") == "True" ){
                divAcc.innerHTML = divAcc.innerHTML + "<div class=\"list-save\"><i class=\"fa-solid fa-file-pen\"></i> Save</div>";
            }

            divCollapse.append(divAcc);
            divGroup.append(divCollapse);

            $("#accordionPanels").append(divGroup);
            $(".sortable-list").sortable();

        }
    });

    <!-- UI Add task -->
    $(document).on('click', ".add-icon", function(){

        numTask = $(this).next(".sortable-list").children("li").length;
        has_value = $(this).prev(".tasks").val();
        console.log(has_value);
        console.log(HtmlEncode(has_value));

        if( has_value && numTask < 10 ){
            htmlString = "<li><input class=\"form-check-input\" type=\"checkbox\" value=\"\"> <span>" + HtmlEncode(has_value) + "</span><i class=\"fa-solid fa-circle-minus del-icon\"></i></li>"
            console.log(htmlString)
            $(this).next(".sortable-list").append(htmlString);
        }

        function HtmlEncode(s)
        {
          var el = document.createElement("div");
          el.innerText = el.textContent = s;
          s = el.innerHTML;
          return s;
        }

    });

    <!-- UI Delete task -->
    $(document).on('click', ".del-icon", function(){
       $(this).parent().remove();
    });

});
