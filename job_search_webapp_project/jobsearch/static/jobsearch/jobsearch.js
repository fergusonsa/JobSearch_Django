function filterNewPostings(thisForm) {

    document.getElementById("filterForm").submit();
}

function submit_interest(posting_id, interest_type, interest_display_name) {

  $.ajax({
    url: '/jobsearch/ajax/' + posting_id + '/' + interest_type,
    data: {},
    dataType: 'json',
    success: function (data) {
      if (data.response != 'success') {
        alert("Attempt to set the interest for the posting '" + posting_id + "' to '"+ interest_type + "' failed! Reason: " + data.response);
      } else if (interest_display_name != null) {
        $(interest_display_name).text(interest_type)
      }
    }
  });
}

